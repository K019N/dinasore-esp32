from machine import Pin
import time


class ESP32_PIN:

    schedule_args = ['self', 'event_name', 'event_value', 'VALUE', 'NUM']
    safe_pins = [4, 13, 14, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]


    def schedule(self, event_name, event_value, VALUE, NUM):
        if event_name == 'REQ':
            if NUM < 0 or NUM > 39:
                return [event_value, 'Invalid PIN number']
            if NUM not in self.safe_pins:
                return [event_value, 'Unsafe PIN']
            led = Pin(NUM, Pin.OUT)
            print(VALUE)
            led.value(VALUE)
            return [event_value, 'OK']
