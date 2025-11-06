import _thread
import time
from core import fb_interface, logging


class FB(fb_interface.FBInterface):

    def __init__(self, fb_name, fb_type, fb_obj, fb_xml):
        fb_interface.FBInterface.__init__(self, fb_name, fb_type, fb_xml)

        self.fb_obj = fb_obj
        self.fb_name = fb_name
        self.thread_id = None
        self.kill_event = False
        self.execution_end = False
        self.lock = _thread.allocate_lock()
        self.running = False

    def start(self):
        logging.info('starting fb {0}...'.format(self.fb_name))
        if self.fb_name == "OUT_ANY_CONSOLE":
            self.input_events["REQ"] = ("Event", None, False)
        print("...EI: ", self.input_events, "...") 
        try:
            self.thread_id = _thread.start_new_thread(self.run, ())
            self.running = True
            return self.thread_id
        except Exception as e:
            logging.error('Failed to start fb thread: {0}'.format(e))
            return None

    def run(self):
        logging.info('fb {0} started.'.format(self.fb_name))

        while not self.kill_event:
            with self.lock:
                self.execution_end = False

            self.wait_event()

            if self.kill_event:
                break

            inputs = self.read_inputs()

            logging.info('running fb...')

            try:
                outputs = self.fb_obj.schedule(*inputs)

            except TypeError as error:
                logging.error('invalid number of arguments (check if fb method args are in fb_type.fbt)')
                logging.error(str(error))
                logging.info('stopping the fb work...')
                break

            except Exception as ex:
                logging.error(str(ex))
                logging.info('stopping the fb work...')
                break

            else:
                if self.kill_event:
                    break

                # self.update_outputs(outputs)

                with self.lock:
                    self.execution_end = True

        with self.lock:
            self.running = False
        logging.info('fb {0} thread finished.'.format(self.fb_name))

    def stop(self):
        logging.info('stopping fb {0}...'.format(self.fb_name))

        self.kill_event = True

        self.push_event('unblock', 1)

        try:
            if hasattr(self.fb_obj, '__del__'):
                self.fb_obj.__del__()
        except AttributeError as exc:
            logging.warning('can not delete the fb object.')
            logging.warning(exc)
        except Exception as exc:
            logging.warning('error during fb object cleanup: {0}'.format(exc))

        max_wait = 5
        wait_count = 0
        while self.running and wait_count < max_wait * 10:
            time.sleep(0.1)
            wait_count += 1

        if self.running:
            logging.warning('fb {0} thread did not stop gracefully'.format(self.fb_name))
        else:
            logging.info('fb {0} stopped.'.format(self.fb_name))

    def is_alive(self):
        with self.lock:
            return self.running

    def wait_execution_end(self, timeout=None):
        start_time = time.time()
        while not self.execution_end:
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.01)
        return True