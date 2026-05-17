import _thread
from collections import OrderedDict
from core import fb_interface, logging
import time

from custom_parser.xml import ElementTree as ETree


GENERIC_TYPES = {
    'ANY', 'ANY_ELEMENTARY', 'ANY_MAGNITUDE', 'ANY_NUM',
    'ANY_INTEGRAL', 'ANY_REAL', 'ANY_INT', 'ANY_UNSIGNED',
    'ANY_SIGNED', 'ANY_BIT', 'ANY_CHARS', 'ANY_CHAR',
    'ANY_STRING', 'ANY_DATE',
}

INT_TYPES = {'SINT', 'INT', 'DINT', 'LINT', 'USINT', 'UINT', 'UDINT', 'ULINT', 'BYTE', 'WORD', 'DWORD', 'LWORD'}
REAL_TYPES = {'REAL', 'LREAL'}


def _strip_type_prefix(value):
    text = str(value)
    if '#' in text:
        return text.split('#', 1)
    return None, text


def _format_concrete_value(value_type, value):
    value_type = value_type.upper()
    prefix, raw_value = _strip_type_prefix(value)

    if value_type == 'BOOL':
        text = str(raw_value).strip().upper()
        return 'TRUE' if text in ('1', 'TRUE', 'T', 'YES', 'Y', 'ON') else 'FALSE'

    if value_type in INT_TYPES:
        try:
            return str(int(raw_value))
        except (ValueError, TypeError):
            return str(raw_value)

    if value_type in REAL_TYPES:
        try:
            return str(float(raw_value))
        except (ValueError, TypeError):
            return str(raw_value)

    if value_type == 'STRING':
        return "'{0}'".format(raw_value)

    if value_type in ('WSTRING', 'WCHAR'):
        return '"{0}"'.format(raw_value)

    if value_type == 'CHAR':
        return "'{0}'".format(raw_value)

    if value_type in ('TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME'):
        return str(value)

    return "'{0}'".format(value) if isinstance(value, str) else str(value)


def _infer_concrete_type(value):
    if isinstance(value, bool):
        return 'BOOL'
    if isinstance(value, float):
        return 'LREAL'
    if isinstance(value, int):
        if -32768 <= value <= 32767:
            return 'INT'
        if -2147483648 <= value <= 2147483647:
            return 'DINT'
        return 'LINT' if value < 0 else 'ULINT'

    prefix, raw_value = _strip_type_prefix(value)
    if prefix:
        return prefix.strip().upper()
    return 'CHAR' if len(str(raw_value)) == 1 else 'STRING'


def format_value_for_watch(value_type, value):
    value_type = value_type.upper()
    if value_type not in GENERIC_TYPES:
        return _format_concrete_value(value_type, value)

    concrete_type = _infer_concrete_type(value)
    formatted = _format_concrete_value(concrete_type, value)

    if concrete_type in ('TIME', 'DATE', 'TIME_OF_DAY', 'DATE_AND_TIME'):
        return formatted

    return '{0}#{1}'.format(concrete_type, formatted)


class MicroEvent:
    def __init__(self):
        self._flag = False
        self._lock = _thread.allocate_lock()
    
    def set(self):
        with self._lock:
            self._flag = True
    
    def clear(self):
        with self._lock:
            self._flag = False
    
    def is_set(self):
        with self._lock:
            return self._flag
    
    def wait(self, timeout=None):
        start = time.time()
        while not self.is_set():
            if timeout is not None and (time.time() - start) > timeout:
                return False
            time.sleep(0.01)
        return True


class FBInterface:

    def __init__(self, fb_name, fb_type, xml_root):

        self.fb_name = fb_name
        self.fb_type = fb_type
        self.stop_thread = False

        self.event_queue = []

        """
        Each events and variables dictionary contains:
        - name (str): event/variable name
        - type (str): INT, REAL, STRING, BOOL
        - watch (boolean): True, False
        """
        self.input_events = OrderedDict()
        self.output_events = OrderedDict()
        self.input_vars = OrderedDict()
        self.output_vars = OrderedDict()

        # checks if is a loop fb
        self.loop_fb = False
        if 'OpcUa' in xml_root.attrib:
            if xml_root.attrib['OpcUa'] == 'DEVICE.SENSOR':
                self.loop_fb = True
        logging.info('parsing the fb interface (inputs/outputs events/vars)')

        # Parse the xml (iterates over the root)
        for Fb in xml_root.children:
            fb = ETree.fromstring(Fb)
            
            # Searches for the interfaces list
            if fb.tag == 'InterfaceList':
                # Iterates over the interface list
                # to find the inputs/outputs
                for interface in fb.children:
                    # interface = ETree.fromstring(Interface)
                    # Input events
                    if interface.tag == 'EventInputs':
                        # Iterates over the input events
                        for event in interface:
                            if event.tag == "Event":
                                event_name = event.attrib['Name']
                                event_type = event.attrib['Type']
                                self.input_events[event_name] = (event_type, None, False)

                    # Output Events
                    elif interface.tag == 'EventOutputs':
                        # Iterates over the output events
                        for event in interface:
                            if event.tag == "Event":
                                event_name = event.attrib['Name']
                                event_type = event.attrib['Type']
                                self.output_events[event_name] = (event_type, None, False)

                    # Input vars
                    elif interface.tag == 'InputVars':
                        # Iterates over the input vars
                        for var in interface:
                            var_name = var.attrib['Name']
                            var_type = var.attrib['Type']
                            self.input_vars[var_name] = (var_type, None, False)

                    # Output vars
                    elif interface.tag == 'OutputVars':
                        # Iterates over the output vars
                        for var in interface:
                            var_name = var.attrib['Name']
                            var_type = var.attrib['Type']
                            self.output_vars[var_name] = (var_type, None, False)

                    # Doesn't expected interface
                    else:
                        logging.error("doesn't expected interface (check interface name in .fbt file)")

        logging.info('parsing successful with:')
        logging.info('input events: {0}'.format(self.input_events))
        logging.info('output events: {0}'.format(self.output_events))
        logging.info('input vars: {0}'.format(self.input_vars))
        logging.info('output vars: {0}'.format(self.output_vars))

        self.output_connections = dict()
        self.new_event = MicroEvent()  
        self.lock = _thread.allocate_lock()
        
    def set_attr(self, name, new_value=None, set_watch=None):
        # Locks the dictionary usage
        self.lock.acquire()
        try:
            # INPUT VAR
            if name in self.input_vars:
                v_type, value, is_watch = self.input_vars[name]
                # Sets the watch
                if set_watch is not None:
                    self.input_vars[name] = (v_type, value, set_watch)
                # Sets the var value
                elif new_value is not None:
                    self.input_vars[name] = (v_type, new_value, is_watch)

            # INPUT EVENT
            elif name in self.input_events:
                event_type, value, is_watch = self.input_events[name]
                # Sets the watch
                if set_watch is not None:
                    self.input_events[name] = (event_type, value, set_watch)
                # Sets the event value
                elif new_value is not None:
                    self.input_events[name] = (event_type, new_value, is_watch)

            # OUTPUT VAR
            elif name in self.output_vars:
                var_type, value, is_watch = self.output_vars[name]
                # Sets the watch
                if set_watch is not None:
                    self.output_vars[name] = (var_type, value, set_watch)
                # Sets the var value
                elif new_value is not None:
                    self.output_vars[name] = (var_type, new_value, is_watch)

            # OUTPUT EVENT
            elif name in self.output_events:
                event_type, value, is_watch = self.output_events[name]
                # Sets the watch
                if set_watch is not None:
                    self.output_events[name] = (event_type, value, set_watch)
                # Sets the event value
                elif new_value is not None:
                    self.output_events[name] = (event_type, new_value, is_watch)

        finally:
            # Unlocks the dictionary usage
            self.lock.release()

    def read_attr(self, name):
        v_type = None
        value = None
        is_watch = None

        # Locks the dictionary usage
        self.lock.acquire()
        try:
            # INPUT VAR
            if name in self.input_vars:
                v_type, value, is_watch = self.input_vars[name]

            # INPUT EVENT
            elif name in self.input_events:
                v_type, value, is_watch = self.input_events[name]

            # OUTPUT VAR
            elif name in self.output_vars:
                v_type, value, is_watch = self.output_vars[name]

            # OUTPUT EVENT
            elif name in self.output_events:
                v_type, value, is_watch = self.output_events[name]

        except KeyError as error:
            logging.error('can not find that fb attribute')
            logging.error(error)

        finally:
            # Unlocks the dictionary usage
            self.lock.release()

        return v_type, value, is_watch

    def add_connection(self, value_name, connection):
        # If already exists a connection
        if value_name in self.output_connections:
            conns = self.output_connections[value_name]
            conns.append(connection)

        # If don't exists any connection with that value
        else:
            conns = [connection]
            self.output_connections[value_name] = conns

    def push_event(self, event_name, event_value):
        time.sleep(0.01)
        if event_value is not None:
            self.event_queue.append((event_name, event_value))
            # Updates the event value
            self.set_attr(event_name, new_value=event_value)
            # Sets the new event
            self.new_event.set()

    def pop_event(self):
        if len(self.event_queue) > 0:
            # pop event
            event_name, event_value = self.event_queue.pop(0)
            return event_name, event_value
        return None, None

    def wait_event(self):
        while len(self.event_queue) <= 0:
            self.new_event.wait()
            # Clears new_event to wait for new events
            self.new_event.clear()
        # Clears new_event to wait for new events
        self.new_event.clear()

    def read_inputs(self):
        logging.info('reading fb inputs...')

        # First convert the vars dictionary to a list
        events_list = []
        event_name, event_value = self.pop_event()
        if event_name is not None:
            self.set_attr(event_name, new_value=event_value)
            events_list.append(event_name)
            events_list.append(event_value)

        # Second converts the event dictionary to a list
        vars_list = []
        logging.info('input vars: {0}'.format(self.input_vars))
        # Get all the vars
        for index, var_name in enumerate(self.input_vars):
            v_type, value, is_watch = self.read_attr(var_name)
            vars_list.append(value)

        # Finally concatenate the 2 lists
        return events_list + vars_list

    def update_outputs(self, outputs):
        logging.info('updating the outputs...')

        # Converts the second part of the list to variables
        for index, var_name in enumerate(self.output_vars):
            # Second part of the list delimited by the events dictionary len
            new_value = outputs[index + len(self.output_events)]

            # Updates the var value
            self.set_attr(var_name, new_value=new_value)

            # Verifies if exist any connection
            if var_name in self.output_connections:
                # Updates the connection
                for connection in self.output_connections[var_name]:
                    connection.update_var(new_value)

        # Converts the first part of the list to events
        for index, event_name in enumerate(self.output_events):
            value = outputs[index]
            self.set_attr(event_name, new_value=value)
            # Verifies if exist any connection
            if event_name in self.output_connections:
                # Sends the event ot the new fb
                for connection in self.output_connections[event_name]:
                    connection.send_event(value)

    def read_watches(self, start_time):
        # Creates the xml root element
        fb_root = ETree.Element('FB', {'name': self.fb_name})

        # Mixes the vars in 1 dictionary
        var_mix = {}
        var_mix.update(self.input_vars)
        var_mix.update(self.output_vars)
        # Iterates over the mix dictionary
        for index, var_name in enumerate(var_mix):
            v_type, value, is_watch = self.read_attr(var_name)
            if is_watch and (value is not None):
                port = ETree.Element('Port', {'name': var_name})
                ETree.SubElement(port, 'Data', {'value': format_value_for_watch(v_type, value),
                                                'forced': 'false'})
                fb_root.append(port)

        # Mixes the vars in 1 dictionary
        event_mix = {}
        event_mix.update(self.input_events)
        event_mix.update(self.output_events)
        # Iterates over the mix dictionary
        for index, event_name in enumerate(event_mix):
            v_type, value, is_watch = self.read_attr(event_name)
            if is_watch and (value is not None):
                port = ETree.Element('Port', {'name': event_name})
                ETree.SubElement(port, 'Data', {'value': str(value)})
                fb_root.append(port)

        # Gets the number of watches
        watches_len = len(fb_root.findall('Port'))

        return fb_root, watches_len


class Connection:

    def __init__(self, destination_fb, value_name):
        self.destination_fb = destination_fb
        self.value_name = value_name

    def update_var(self, value):
        self.destination_fb.set_attr(self.value_name, new_value=value)

    def send_event(self, value):
        self.destination_fb.push_event(self.value_name, value)
