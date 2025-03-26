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
button_debounce_time = 400  # 400ms debounce for smooth interaction
idle_time = 30000 # 30 seconds of idle time before menu resets
camera_on = False # Used for determining whether to have the camera on or off

# Setup camera.
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.LCD)
sensor.skip_frames()

# Initialize and clear the display
lcd = display.SPIDisplay()
lcd.clear()
time.sleep(1)

# Define multiple menus as image lists
title_screen = ["2.jpg"]
main_menu = ["14.jpg", "15.jpg", "16.jpg"]
manual_menu = ["17.jpg", "18.jpg", "19.jpg", "20.jpg", "21.jpg", ]
objrec_menu = ["35.jpg"]
calib_menu = ["3.jpg"]

cyl_menu = ["23.jpg", "24.jpg", "25.jpg"]
sphere_menu = ["27.jpg", "28.jpg", "29.jpg"]
pinch_menu = ["31.jpg", "32.jpg", "33.jpg"]

gripping_screen = ["34.jpg"]

camera_mode = sensor.snapshot()

# Define links between menus based on selection index
menu_links = {
    "title_screen": {0: "main_menu"},
    "main_menu": {0: "manual_menu", 1: "objrec_menu", 2: "calib_menu"},
    "manual_menu": {1: "cyl_menu", 2: "sphere_menu", 3: "pinch_menu", 4: "main_menu"},
    "objrec_menu": {0: "camera_mode"},
    "cyl_menu": {0: "gripping_screen", 1: "gripping_screen", 2: "manual_menu"},
    "sphere_menu": {0: "gripping_screen", 1: "gripping_screen", 2: "manual_menu"},
    "pinch_menu": {0: "gripping_screen", 1: "gripping_screen", 2: "manual_menu"},
}

# Track the current menu and index
current_menu = "title_screen"
menu_stack = ["title_screen"]  # Stack to track navigation history
current_index = 0  # Current selection

# Joystick normalization constants
ADC_MAX = 65535
CENTER = ADC_MAX // 2
DEADZONE = 5000
THRESHOLD = 15000
MOVE_DELAY = 200  # Delay to prevent rapid flicking

# Function to select a multiplexer channel
def select_mux_channel(channel):
    s0.value(channel & 0x01)
    s1.value((channel >> 1) & 0x01)
    s2.value((channel >> 2) & 0x01)
    s3.value((channel >> 3) & 0x01)
    time.sleep_us(10)  # Small delay to stabilize reading

# Read joystick X and Y values through the multiplexer
def read_joystick():
    select_mux_channel(6)  # Read X-axis
    x_val = adc.read_u16() - CENTER

    select_mux_channel(7)  # Read Y-axis
    y_val = adc.read_u16() - CENTER

    if abs(x_val) < DEADZONE:
        x_val = 0
    if abs(y_val) < DEADZONE:
        y_val = 0

    if x_val > THRESHOLD:
        return "RIGHT"
    elif x_val < -THRESHOLD:
        return "LEFT"
    elif y_val > THRESHOLD:
        return "DOWN"
    elif y_val < -THRESHOLD:
        return "UP"
    else:
        return "CENTER"

def display_camera_feed():
    while current_menu == "camera_mode":
        lcd.write(sensor.snapshot())

# Handle joystick movement and button presses
last_move_time = time.ticks_ms()

while True:
    move_direction = read_joystick()
    current_time = time.ticks_ms()
    menu = globals()[current_menu]  # Get current menu images dynamically

    # Idle Timeout Check
    if time.ticks_diff(current_time, last_move_time) > idle_time and current_menu != "title_screen":
        current_menu = "title_screen"
        menu_stack = ["title_screen"]  # Reset menu history
        current_index = 0
        last_move_time = current_time  # Reset idle timer

    # Handle joystick movement
    if time.ticks_diff(current_time, last_move_time) > MOVE_DELAY:
        if move_direction == "RIGHT":
            current_index = (current_index + 1) % len(menu)
            last_move_time = current_time
        elif move_direction == "LEFT":
            current_index = (current_index - 1) % len(menu)
            last_move_time = current_time
        elif move_direction == "DOWN" and len(menu_stack) > 1:
            menu_stack.pop()  # Remove last menu
            current_menu = menu_stack[-1]  # Go back to previous menu
            current_index = 0
            time.sleep(0.2)

    # Check for button press to switch menus based on selected image
    button_state = button.value()
    if button_state == 0 and button_last_state == 1:  # Button just pressed
        if time.ticks_diff(time.ticks_ms(), last_button_time) > button_debounce_time:
            if current_menu in menu_links and current_index in menu_links[current_menu]:
                current_menu = menu_links[current_menu][current_index]  # Get next menu
                menu_stack.append(current_menu)  # Save menu history
                current_index = 0  # Reset selection in the new menu
            last_button_time = time.ticks_ms()
            continue

    button_last_state = button_state

    # Enter Camera Mode if in object recognition menu
    if current_menu == "objrec_menu":
        display_camera_feed()
        current_menu = "main_menu"
        current_index = 0
    else:
        # Display the selected image
        img = image.Image(menu[current_index])
        lcd.write(img, hint=image.SCALE_ASPECT_KEEP)

    time.sleep(0.05)  # Small delay for stability
