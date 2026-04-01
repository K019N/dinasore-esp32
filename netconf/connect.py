import network
import time

from netconf.config import SSID, PASSWORD

def wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    print("Connecting to Wi-Fi...")
    sta_if.connect(SSID, PASSWORD)

    timeout = 10 
    while not sta_if.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1
        print("Waiting for connection...")

    if sta_if.isconnected():
        print("Successfully connected!")
        ip_address = sta_if.ifconfig()[0]
        print("Local IP address:", ip_address)
        return ip_address
    else:
        print("Failed to connect to Wi-Fi")
        return None

