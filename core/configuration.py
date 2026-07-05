import gc
from core import fb_resources
from core import fb
from core import fb_interface
from core import fb_interface, logging
from custom_parser.xml import ElementTree as ETree


class Configuration:

    def __init__(self, config_id, config_type):
        self.fb_dictionary = dict()
        self.config_id = self.normalize_fb_name(config_id)
        self.stopped = False
        self.create_fb('START', config_type)

    @staticmethod
    def normalize_fb_name(fb_name):
        if fb_name is None:
            return fb_name
        return fb_name.rsplit('.', 1)[-1]

    @staticmethod
    def normalize_fb_type(fb_type):
        if fb_type is None:
            return fb_type
        return fb_type.rsplit('::', 1)[-1]

    @staticmethod
    def split_endpoint(endpoint):
        parts = endpoint.split('.')
        if len(parts) < 2:
            return endpoint, None
        return parts[-2], parts[-1]

    def get_fb(self, fb_name):
        fb_element = None
        fb_name = self.normalize_fb_name(fb_name)
        try:
            fb_element = self.fb_dictionary[fb_name]
        except KeyError as error:
            logging.error('can not find that fb {0}'.format(fb_name))
            logging.error(str(error))

        return fb_element

    def set_fb(self, fb_name, fb_element):
        fb_name = self.normalize_fb_name(fb_name)
        self.fb_dictionary[fb_name] = fb_element

    def exists_fb(self, fb_name):
        fb_name = self.normalize_fb_name(fb_name)
        return fb_name in self.fb_dictionary

    def create_fb(self, fb_name, fb_type, init=True):
        logging.info('creating a new fb...')
        display_fb_name = fb_name
        fb_name = self.normalize_fb_name(fb_name)
        fb_type = self.normalize_fb_type(fb_type)

        fb_res = fb_resources.FBResources(fb_type)
        exists_fb = fb_res.exists_fb()

        if not exists_fb:
            logging.info('fb does not exist, needs to be downloaded...')

        fb_definition, fb_obj = fb_res.import_fb()

        if fb_definition is None:
            logging.error('cannot create fb type: {0}, instance: {1}'.format(fb_type, fb_name))
            return None, None

        # Проверка соответствия аргументов функции schedule (если возможно)
        if hasattr(fb_obj, 'schedule'):
            schedule_func = fb_obj.schedule

            # В MicroPython нет introspection, поэтому используем метаданные,
            # если они заданы в объекте Function Block
            schedule_args = getattr(fb_obj, 'schedule_args', None)

            if schedule_args is not None:
                # Приводим имена аргументов к нижнему регистру
                schedule_args = [arg.lower() for arg in schedule_args]

                # Извлекаем список входных переменных из XML
                xml_args = []
                for child in fb_definition:
                    input_vars = child.find('InputVars')
                    if input_vars is None:
                        continue
                    vars_list = input_vars.findall('VarDeclaration')
                    for xml_var in vars_list:
                        var_name = xml_var.get('Name')
                        if var_name is not None:
                            xml_args.append(var_name.lower())
                        else:
                            logging.error(
                                'Missing "Name" attribute for variable. Please check {0}.fbt'.format(fb_name)
                            )

                # Сравнение аргументов schedule и XML
                if schedule_args != xml_args:
                    logging.warning(
                        'Argument names for schedule() of {0} do not match definition in {0}.fbt'.format(fb_name)
                    )
                    logging.warning(
                        'Ensure variable arguments match the InputVars order and names.'
                    )

        # Создание FB-элемента
        fb_element = fb.FB(display_fb_name, fb_type, fb_obj, fb_definition)
        self.set_fb(fb_name, fb_element)
        logging.info('created fb type: {0}, instance: {1}'.format(fb_type, display_fb_name))

        # Инициализация (если требуется)
        if init:
            self.create_connection('START.COLD', '{0}.INIT'.format(fb_name))

        # Создание петли для циклического FB (если применимо)
        if getattr(fb_element, 'loop_fb', False):
            loop_fb_name = '{0}_LOOP1'.format(fb_name)
            self.create_fb(loop_fb_name, 'SLEEP', init=False)
            self.create_connection('{0}.READ_O'.format(fb_name), '{0}.SLEEP'.format(loop_fb_name))
            self.create_connection('{0}.SLEEP_O'.format(loop_fb_name), '{0}.READ'.format(fb_name))

        return fb_element, fb_definition

    def create_connection(self, source, destination):
        logging.info('creating a new connection...')

        source_fb_name, source_name = self.split_endpoint(source)
        destination_fb_name, destination_name = self.split_endpoint(destination)

        source_fb = self.get_fb(source_fb_name)
        destination_fb = self.get_fb(destination_fb_name)
        
        if not destination_fb:
            logging.error("No block matches {0}".format(destination_fb_name))
            logging.error("Couldnt create connection")
            return

        if not source_fb:
            logging.error("No block matches {0}".format(source_fb_name))
            logging.error("Couldnt create connection")
            return

        connection = fb_interface.Connection(destination_fb, destination_name)
        source_fb.add_connection(source_name, connection)

        logging.info('connection created between {0} and {1}'.format(source, destination))

    def create_watch(self, source, destination):
        logging.info('creating a new watch...')

        source_fb_name, source_name = self.split_endpoint(source)
        source_fb = self.get_fb(source_fb_name)

        try:
            source_fb.set_attr(source_name, set_watch=True)
        except AttributeError as error:
            # check if the return if None
            logging.error(str(error))
            logging.error("don't forget to delete the watch when you delete a function block")

        logging.info('watch created between {0} and {1}'.format(source, destination))

    def delete_watch(self, source, destination):
        logging.info('deleting a new watch...')

        source_fb_name, source_name = self.split_endpoint(source)
        source_fb = self.get_fb(source_fb_name)

        try:
            source_fb.set_attr(source_name, set_watch=False)
        except AttributeError as error:
            # check if the return if None
            logging.error(str(error))
            logging.error("don't forget to delete the watch when you delete a function block")

        logging.info('watch deleted between {0} and {1}'.format(source, destination))

    def write_connection(self, source_value, destination):
        logging.info('writing a connection...')
        destination_fb_name, destination_name = self.split_endpoint(destination)
        
        destination_fb = self.get_fb(destination_fb_name)
        
        if not destination_fb:
            logging.error("No block matches {0}".format(destination_fb_name))
            logging.error("Couldnt write connection")
            return

        v_type, value, is_watch = destination_fb.read_attr(destination_name)

        # Verifies if is to write an event
        if source_value == '$e':
            logging.info('writing an event...')
            if value is not None:
                # If the value is not None increment
                destination_fb.push_event(destination_name, value + 1)
            else:
                # If the value is None push 1
                destination_fb.push_event(destination_name, 1)

        # Writes a hardcoded value
        else:
            logging.info('writing a hardcoded value...')
            value_to_set = self.convert_type(source_value, v_type)
            destination_fb.set_attr(destination_name, value_to_set)

        logging.info('connection ({0}) configured with the value {1}'.format(destination, source_value))
        self.process_pending_events()

    def process_pending_events(self):
        progressed = True
        while progressed and not self.stopped:
            progressed = False
            for fb_name, fb_element in list(self.fb_dictionary.items()):
                if self.stopped:
                    break
                if fb_name == 'START':
                    continue

                if not getattr(fb_element, 'event_queue', None):
                    continue

                if not fb_element.is_alive():
                    fb_element.start()

                try:
                    fb_element.run()
                    progressed = True
                except Exception as exc:
                    logging.error('fb execution failed for {0}: {1}'.format(fb_name, exc))

    def read_watches(self, start_time):
        logging.info('reading watches...')

        resources_xml = ETree.Element('Resource', {'name': self.config_id})

        for fb_name, fb_element in self.fb_dictionary.items():
            fb_xml, watches_len = fb_element.read_watches(start_time)

            if watches_len > 0:
                resources_xml.append(fb_xml)

        fb_watches_len = len(resources_xml.findall('FB'))
        return resources_xml, fb_watches_len

    def start_work(self):
        logging.info('starting the fb flow...')
        if not self.get_fb('START'):
            logging.error("CRITICAL no START block found")
            return

        self.stopped = False
        start_fb = self.get_fb('START')
        start_fb.start()

        try:
            outputs = start_fb.fb_obj.schedule()
            start_fb.update_outputs(outputs)
        except Exception as exc:
            logging.error('start block execution failed: {0}'.format(exc))
            return

        self.process_pending_events()

    def stop_work(self):
        logging.info('stopping the fb flow...')
        self.stopped = True
        for fb_name, fb_element in list(self.fb_dictionary.items()):
            if fb_name != 'START':
                fb_element.stop()
        self.fb_dictionary = {}
        gc.collect()

    @staticmethod
    def convert_type(value, value_type):
        converted_value = None

        # String variable
        if value_type == 'WSTRING' or value_type == 'STRING' or value_type == 'ANY' or value_type == 'TIME':
            converted_value = value

        # Boolean variable
        elif value_type == 'BOOL':
            # Checks if is true
            if value == '1' or value == 'true' or value == 'True' or value == 'TRUE' or value == 't':
                converted_value = True
            # Checks if is false
            elif value == '0' or value == 'false' or value == 'False' or value == 'FALSE' or value == 'f':
                converted_value = False

        # Integer variable
        elif value_type == 'UINT' or value_type == 'Event' or value_type == 'INT':
            converted_value = int(value)

        # Float variable
        elif value_type == 'REAL' or value_type == 'LREAL':
            converted_value = float(value)

        return converted_value
