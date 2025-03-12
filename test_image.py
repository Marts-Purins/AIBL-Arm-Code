import time
import image
import display
import sensor
from machine import Pin, ADC

###### Multiplexer Definitions ######

# Setup multiplexer control pins (selects which channel to read from)
s0 = Pin('P1', Pin.OUT)
s1 = Pin('P9', Pin.OUT)
s2 = Pin('P10', Pin.OUT)
s3 = Pin('P11', Pin.OUT)

# Analog pin to read the multiplexer output
adc = ADC(Pin('P6'))  # Joystick X and Y values are read from P6

###### 5D Button Definitions ######

# Joystick button setup
button = Pin('P13', Pin.IN, Pin.PULL_UP)  # Button connected to GPIO

# Debounce variables
button_last_state = 1
last_button_time = 0  # Track last button press time
button_debounce_time = 200  # 200ms debounce for smooth interaction

# Setup camera.
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.LCD)
sensor.skip_frames()

# Initialize and clear the display
lcd = display.SPIDisplay()
lcd.clear()
time.sleep(1)

# Load images from the SD card
images = ["monster.jpg", "1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg", "6.jpg"]
current_index = 0

# Constants for joystick normalization
ADC_MAX = 65535  # Maximum ADC value (16-bit)
CENTER = ADC_MAX // 2  # Midpoint (32,768)
Deadband = 5000  # Ignore small fluctuations
Threshold = 15000  # Sensitivity for movement detection
MOVE_DELAY = 200  # Minimum delay (ms) between image changes

# Function to select a multiplexer channel
def select_mux_channel(channel):
    s0.value(channel & 0x01)
    s1.value((channel >> 1) & 0x01)
    s2.value((channel >> 2) & 0x01)
    s3.value((channel >> 3) & 0x01)
    time.sleep_us(10)

# Read joystick X and Y values through the multiplexer
def read_joystick():
    select_mux_channel(6)  # Select channel for X-axis
    x_val = adc.read_u16() - CENTER  # Normalize: -32,768 to +32,768

    select_mux_channel(7)  # Select channel for Y-axis
    y_val = adc.read_u16() - CENTER  # Normalize: -32,768 to +32,768

    # Apply deadzone filter
    if abs(x_val) < Deadband:
        x_val = 0
    if abs(y_val) < Deadband:
        y_val = 0

    # Determine movement direction
    if x_val > Threshold:
        return "RIGHT"
    elif x_val < -Threshold:
        return "LEFT"
    elif y_val > Threshold:
        return "DOWN"
    elif y_val < -Threshold:
        return "UP"
    else:
        return "CENTER"

# Function to handle joystick movement and button press
last_move_time = time.ticks_ms()

while True:
    # Read joystick position
    move_direction = read_joystick()
    current_time = time.ticks_ms()

    # Handle joystick movement with a controlled delay
    if time.ticks_diff(current_time, last_move_time) > MOVE_DELAY:
        if move_direction == "RIGHT":
            current_index = (current_index + 1) % len(images)
            last_move_time = current_time
        elif move_direction == "LEFT":
            current_index = (current_index - 1) % len(images)
            last_move_time = current_time

    # Check joystick button press with non-blocking debounce
    button_state = button.value()
    if button_state == 0 and button_last_state == 1:
        if time.ticks_diff(time.ticks_ms(), last_button_time) > button_debounce_time:
            print("Joystick button pressed! Resetting to first image.")
            current_index = 0  # Reset to first image
            last_button_time = time.ticks_ms()

    button_last_state = button_state  # Update button state

    # Display the selected image
    img = image.Image(images[current_index])
    lcd.write(img, hint=image.SCALE_ASPECT_KEEP)
