import time

class OUT_ANY_CONSOLE:

    def schedule(self, event_name, event_value, QI, label, in_data):
        # if event_name == 'REQ' and QI == True:
        if event_name == 'REQ':
            print(f"{time.ctime()}# {label}: {in_data}")
            return [event_value, 1]
