import time



class DELAY_MS:

    schedule_args = ['self', 'event_name', 'event_value', 'IN']

    def schedule(self, event_name, event_value, IN):
        if event_name == 'REQ':
            print("sleep")
            time.sleep(IN)
            print("unsleep")
            return [event_value]
