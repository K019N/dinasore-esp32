import _thread
from core import logging
from core import request_profiler
from core import thread_utils
import time


class ClientThread:

    def __init__(self, connection, client_address, config_m):
        self.config_m = config_m
        self.connection = connection
        self.client_address = client_address
        self.thread_id = None
        self.name = '{0}:{1}'.format(client_address[0], client_address[1])

    def start(self):
        try:
            thread_utils.set_thread_stack_size(thread_utils.CLIENT_THREAD_STACK)
            self.thread_id = _thread.start_new_thread(self.run, ())
            logging.info('Started thread for client {0}'.format(self.name))
            return self.thread_id
        except Exception as e:
            logging.error('Failed to start thread for {0}: {1}'.format(self.name, e))
            return None

    def run(self):
        try:
            logging.info('Connection from {0}'.format(self.client_address))
            # Receive the data in small chunks and retransmit it
            while True:
                data = self.connection.recv(2048)
                logging.info('Received request bytes: {0}'.format(len(data) if data else 0))
                if data:
                    total_start = request_profiler.start_timer()
                    process_start = request_profiler.start_timer()
                    response = None
                    try:
                        response = self.parse_request(data)
                        process_ms = request_profiler.elapsed_ms(process_start)
                        logging.info('Sending response bytes: {0}'.format(len(response) if response else 0))
                        self.connection.sendall(response)
                        total_ms = request_profiler.elapsed_ms(total_start)
                        request_profiler.log_request(self.name, data, response, process_ms, total_ms)
                    except Exception as e:
                        process_ms = request_profiler.elapsed_ms(process_start)
                        total_ms = request_profiler.elapsed_ms(total_start)
                        request_profiler.log_request(self.name, data, response, process_ms, total_ms,
                                                     status='ERROR', error=str(e))
                        raise
                else:
                    logging.info('No more data from {0}'.format(self.client_address))
                    break

        except Exception as e:
            logging.error('Error in client thread {0}: {1}'.format(self.name, e))
        finally:
            # Clean up the connection
            try:
                self.connection.close()
            except:
                pass
            logging.info('Connection closed for {0}'.format(self.client_address))

    def parse_request(self, data):
        config_id_size = int(data[1:3].hex(), 16)
        request_start = data.find(b'<Request')

        if request_start >= 0:
            xml_data = self.remove_service_symbols(data[request_start:].decode('utf-8'))
        else:
            xml_data = None

        if config_id_size == 0:
            data_str = xml_data if xml_data is not None else data[6:].decode('utf-8')
            response = self.config_m.parse_general(data_str)
        else:
            config_id = data[3: config_id_size + 3].decode('utf-8')
            data_str = xml_data if xml_data is not None else data[config_id_size + 3 + 3:].decode('utf-8')
            response = self.config_m.parse_configuration(data_str, config_id)

        return response

    @staticmethod
    def remove_service_symbols(data):
        if "&apos;" in data:
            data = data.replace('&apos;', '')
        elif "&quote;" in data:
            data = data.replace('&quote;', '')
        return data

    def is_alive(self):
        return True 
