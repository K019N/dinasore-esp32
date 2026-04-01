import _thread
from core import logging
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
                logging.info('Received {0}'.format(data))
                if data:
                    response = self.parse_request(data)
                    logging.info('Sending response {0}'.format(response))
                    self.connection.sendall(response)
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

        if config_id_size == 0:
            data_str = data[6:].decode('utf-8')
            response = self.config_m.parse_general(data_str)
        else:
            config_id = data[3: config_id_size + 3].decode('utf-8')
            data_str = data[config_id_size + 3 + 3:].decode('utf-8')
            response = self.config_m.parse_configuration(data_str, config_id)

        return response

    def is_alive(self):
        return True 