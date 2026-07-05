import time

class E_DELAY:
    
    schedule_args = ['self','event_name', 'event_value', 'DT']

    def schedule(self, event_name, event_value, DT):
        if event_name == 'START':
            delay = 0.0
            if 'ms' in DT:
                delay = float("".join(filter(str.isdigit, DT))) / 1000
            elif 'ns' in DT:
                delay = float("".join(filter(str.isdigit, DT))) / 10**9
            else:
                delay = "".join(filter(str.isdigit, DT))

            print(delay)
            time.sleep(delay)
            return [event_value]
        elif event_name == 'STOP':
            return [event_value - 1]
