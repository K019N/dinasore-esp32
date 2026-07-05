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
        self.running = False

    def start(self):
        logging.info('starting fb {0}...'.format(self.fb_name))
        self.running = True
        self.kill_event = False
        return 1

    def run(self):
        logging.info('fb {0} started.'.format(self.fb_name))
        self.execution_end = False

        if self.kill_event:
            self.running = False
            return

        if len(self.event_queue) <= 0:
            self.execution_end = True
            self.running = False
            logging.info('fb {0} has no pending events, skipping.'.format(self.fb_name))
            return

        inputs = self.read_inputs()
        logging.info('running fb...')

        try:
            outputs = self.fb_obj.schedule(*inputs)
            if outputs is None:
                outputs = []
        except TypeError as error:
            logging.error('invalid number of arguments (check if fb method args are in fb_type.fbt)')
            logging.error(str(error))
            self.running = False
            return
        except Exception as ex:
            logging.error(str(ex))
            self.running = False
            return

        try:
            self.update_outputs(outputs)
        except Exception as ex:
            logging.error('error while updating outputs: {0}'.format(ex))

        self.execution_end = True
        self.running = False
        logging.info('fb {0} finished.'.format(self.fb_name))

    def stop(self):
        logging.info('stopping fb {0}...'.format(self.fb_name))

        self.kill_event = True

        try:
            if hasattr(self.fb_obj, '__del__'):
                self.fb_obj.__del__()
        except AttributeError as exc:
            logging.warning('can not delete the fb object.')
            logging.warning(exc)
        except Exception as exc:
            logging.warning('error during fb object cleanup: {0}'.format(exc))

        self.running = False
        logging.info('fb {0} stopped.'.format(self.fb_name))

    def is_alive(self):
        return self.running

    def wait_execution_end(self, timeout=None):
        return True
