import time
import machine
from machine import Pin

###### 5D Button Definitions ######

# Setup the button for wake-up
button = Pin('P13', Pin.IN, Pin.PULL_UP)  # Button connected to GPIO 5

# Debounce variables
button_last_state = 1
button_press_time = 0
long_press_duration = 5000  # 5 seconds (in ms)

###### 5D Button Definitions ######

# Callback for waking up the device
def wake_up(pin):
    print("Button Pressed...")

# Attach wake-up callback
button.irq(trigger=Pin.IRQ_FALLING, handler=wake_up)

# Function to enter deep sleep mode
def enter_deep_sleep():
    print("Entering deep sleep mode...")
    time.sleep(0.5)  # Allow UART to print before sleeping
    #deepsleep()  # Put the device into deep sleep mode
    machine.soft_reset()
