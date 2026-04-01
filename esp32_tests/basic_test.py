import os
import sys

try:
    current_path = sys.path[0] if sys.path else ''
    new_path = os.path.join(os.path.dirname(current_path)) if current_path else '/dinasore'
    
    # Проверяем, что путь не пустой и не добавляем дубликаты
    if new_path and new_path not in sys.path:
        sys.path.append(new_path)
        print("Добавлен путь:", new_path)
    else:
        print("Путь уже существует или пустой")
        
except Exception as e:
    print("Ошибка при добавлении пути:", e)
    
    
    
from core import configuration
import time
from core import logging
    
    

class TestFB():

    def setUp(self):
        # Configure the logging output
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s][%(levelname)s][%(threadName)s] %(message)s')

        self.conf = configuration.Configuration('config_1', 'EMB_RES')

    def test_fb_creation(self):
        self.conf.create_fb('E_EXAMPLE_1', 'TEST_FB', init=False)

        fb = self.conf.fb_dictionary['E_EXAMPLE_1']


    def test_fb_connection(self):
        self.conf.create_fb('E_EXAMPLE_1', 'TEST_FB', init=False)
        self.conf.create_fb('E_EXAMPLE_2', 'TEST_FB', init=False)

        self.conf.create_connection('E_EXAMPLE_1.EO0', 'E_EXAMPLE_2.EI')

        fb_1 = self.conf.get_fb('E_EXAMPLE_1')

        fb_2 = self.conf.get_fb('E_EXAMPLE_2')

        connection = fb_1.output_connections['EO0'][0]

    def test_fb_running(self):
        self.conf.create_fb('E_EXAMPLE_1', 'OUT_ANY_CONSOLE', init=False)
        self.conf.start_work()

        fb = self.conf.get_fb('E_EXAMPLE_1')
        # fb.input_events["EI"] = ("Event", None, False)
        # fb.input_vars["G"] = ("BOOL", None, False)
        
        time.sleep(1)
        fb.push_event('REQ', 1)

        time.sleep(0.1)

        # Validate the inputs
        event_type, value, is_watch = fb.input_events['REQ']
        var_type, value, is_watch = fb.input_vars['IN']
        
        self.conf.stop_work()
        
if __name__ == "__main__":
    test = TestFB()
    test.setUp()
    test.test_fb_running()
    