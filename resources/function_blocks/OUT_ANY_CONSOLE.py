import time

class OUT_ANY_CONSOLE:
    
    schedule_args = ['self','event_name', 'event_value', 'QI', 'LABEL', 'IN']

    def schedule(self, event_name, event_value, QI, LABEL, IN):
        # if event_name == 'REQ' and QI == True:
        print("out_any_console")
        if event_name == 'REQ':
            print(f"T#{time.time()}\tINFO: {LABEL}: {IN}")
            return [event_value, 1]
