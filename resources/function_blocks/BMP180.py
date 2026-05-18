try:
    from machine import Pin, I2C
except ImportError:
    Pin = None
    I2C = None

import time


class BMP180:
    schedule_args = ['self', 'event_name', 'event_value', 'I2C_ID', 'SCL', 'SDA', 'OSS', 'ADDR']
    _DEFAULT_ADDR = 0x77
    _DEFAULT_FREQ = 100000

    def __init__(self):
        self.i2c = None
        self.addr = self._DEFAULT_ADDR
        self.calibration = None
        self.current_config = None

    def schedule(self, event_name, event_value, I2C_ID, SCL, SDA, OSS, ADDR):
        if event_name != 'REQ':
            return [None, None, None, None, 'NO_REQ']

        if I2C is None or Pin is None:
            return [event_value, None, None, None, 'NO_MACHINE_MODULE']

        if SCL is None or SDA is None:
            return [event_value, None, None, None, 'MISSING_PINS']

        if OSS is None:
            OSS = 0
        else:
            try:
                OSS = int(OSS)
            except Exception:
                OSS = 0

        if OSS < 0 or OSS > 3:
            OSS = 0

        if ADDR is None or ADDR == 0:
            addr = self._DEFAULT_ADDR
        else:
            addr = int(ADDR)

        try:
            self._ensure_i2c(int(I2C_ID or 0), int(SCL), int(SDA), addr)
            if self.calibration is None:
                self.calibration = self._read_calibration()

            ut = self._read_raw_temperature()
            up = self._read_raw_pressure(OSS)
            temperature, pressure = self._calculate_measurements(ut, up, OSS)
            altitude = self._pressure_to_altitude(pressure)

            return [event_value, temperature, pressure, altitude, 'OK']

        except Exception as exc:
            return [event_value, None, None, None, 'ERR:{0}'.format(str(exc))]

    def _ensure_i2c(self, i2c_id, scl_pin, sda_pin, addr):
        config = (i2c_id, scl_pin, sda_pin, addr)
        if self.i2c is None or self.current_config != config:
            self.i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=self._DEFAULT_FREQ)
            self.addr = addr
            self.current_config = config
            self.calibration = None

    def _read_calibration(self):
        return {
            'AC1': self._read_s16(0xAA),
            'AC2': self._read_s16(0xAC),
            'AC3': self._read_s16(0xAE),
            'AC4': self._read_u16(0xB0),
            'AC5': self._read_u16(0xB2),
            'AC6': self._read_u16(0xB4),
            'B1': self._read_s16(0xB6),
            'B2': self._read_s16(0xB8),
            'MB': self._read_s16(0xBA),
            'MC': self._read_s16(0xBC),
            'MD': self._read_s16(0xBE),
        }

    def _read_u16(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return (data[0] << 8) | data[1]

    def _read_s16(self, reg):
        val = self._read_u16(reg)
        return val - 65536 if val > 32767 else val

    def _write_u8(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))

    def _read_raw_temperature(self):
        self._write_u8(0xF4, 0x2E)
        time.sleep_ms(5)
        return self._read_u16(0xF6)

    def _read_raw_pressure(self, oss):
        self._write_u8(0xF4, 0x34 + (oss << 6))
        delay = 5 if oss == 0 else 8 if oss == 1 else 14 if oss == 2 else 26
        time.sleep_ms(delay)
        data = self.i2c.readfrom_mem(self.addr, 0xF6, 3)
        raw = (data[0] << 16) | (data[1] << 8) | data[2]
        return raw >> (8 - oss)

    def _calculate_measurements(self, ut, up, oss):
        c = self.calibration
        x1 = ((ut - c['AC6']) * c['AC5']) >> 15
        x2 = (c['MC'] << 11) // (x1 + c['MD'])
        b5 = x1 + x2
        temperature = ((b5 + 8) >> 4) / 10.0

        b6 = b5 - 4000
        x1 = (c['B2'] * ((b6 * b6) >> 12)) >> 11
        x2 = (c['AC2'] * b6) >> 11
        x3 = x1 + x2
        b3 = (((c['AC1'] * 4 + x3) << oss) + 2) >> 2
        x1 = (c['AC3'] * b6) >> 13
        x2 = (c['B1'] * ((b6 * b6) >> 12)) >> 16
        x3 = ((x1 + x2) + 2) >> 2
        b4 = (c['AC4'] * (x3 + 32768)) >> 15
        b7 = (up - b3) * (50000 >> oss)
        pressure = (b7 * 2 // b4) if b7 < 0x80000000 else (b7 // b4) * 2
        x1 = (pressure >> 8) * (pressure >> 8)
        x1 = (x1 * 3038) >> 16
        x2 = (-7357 * pressure) >> 16
        pressure = pressure + ((x1 + x2 + 3791) >> 4)
        return temperature, float(pressure)

    def _pressure_to_altitude(self, pressure_pa):
        if pressure_pa is None or pressure_pa <= 0:
            return None
        return 44330.0 * (1.0 - (pressure_pa / 101325.0) ** 0.1903)
