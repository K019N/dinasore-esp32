

class TEST_FB:
    
    schedule_args = ['self','event_name', 'event_value','G']

    def __init__(self):
        self.G_EI = 0

    def schedule(self, event_name, event_value, G):
        if event_name == 'EI':
            self.G_EI = event_value + 1
            EO1 = None
            print("WORKING")
            return [self.G_EI, EO1]
