import time
import image
import display
import sensor
from machine import Pin, ADC, I2C

###### Object Detection Functions ######
# Edge Impulse - OpenMV FOMO Object Detection Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, image, time, ml, math, uos, gc

def fomo_post_process(model, inputs, outputs):
    ob, oh, ow, oc = model.output_shape[0]

    x_scale = inputs[0].roi[2] / ow
    y_scale = inputs[0].roi[3] / oh

    scale = min(x_scale, y_scale)

    x_offset = ((inputs[0].roi[2] - (ow * scale)) / 2) + inputs[0].roi[0]
    y_offset = ((inputs[0].roi[3] - (ow * scale)) / 2) + inputs[0].roi[1]

    l = [[] for i in range(oc)]

    for i in range(oc):
        img = image.Image(outputs[0][0, :, :, i] * 255)
        blobs = img.find_blobs(
            threshold_list, x_stride=1, y_stride=1, area_threshold=1, pixels_threshold=1
        )
        for b in blobs:
            rect = b.rect()
            x, y, w, h = rect
            score = (
                img.get_statistics(thresholds=threshold_list, roi=rect).l_mean() / 255.0
            )
            x = int((x * scale) + x_offset)
            y = int((y * scale) + y_offset)
            w = int(w * scale)
            h = int(h * scale)
            l[i].append((x, y, w, h, score))
    return l

net = None
labels = None
min_confidence = 0.6

try:
    # load the model, alloc the model file on the heap if we have at least 64K free after loading
    net = ml.Model("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
except Exception as e:
    raise Exception('Failed to load "trained.tflite", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

colors = [ # Add more colors if you are detecting more than 7 types of classes at once.
    (255,   0,   0),
    (  0, 255,   0),
    (255, 255,   0),
    (  0,   0, 255),
    (255,   0, 255),
    (  0, 255, 255),
    (255, 255, 255),
]

threshold_list = [(math.ceil(min_confidence * 255), 255)]

def objectDetection():
    lcd.clear()
    time.sleep(1)

    cylChk = 0
    sphereChk = 0
    pinchChk = 0

    targetGrip = cylinderGrip

    clock = time.clock()
    while(True):
        clock.tick()

        img = sensor.snapshot()

        for i, detection_list in enumerate(net.predict([img], callback=fomo_post_process)):
            if i == 0: continue  # background class
            if len(detection_list) == 0: continue  # no detections for this class?

            #print("********** %s **********" % labels[i])
            for x, y, w, h, score in detection_list:
                center_x = math.floor(x + (w / 2))
                center_y = math.floor(y + (h / 2))
                #print(f"x {center_x}\ty {center_y}\tscore {score}")
                img.draw_circle((center_x, center_y, 12), color=colors[i])


        if labels[i] in ['gatorade', 'monster', 'water']:
            cylChk += 1
        elif labels[i] == 'creamer':
            sphereChk += 1
        else:
            pinchChk += 1

        if cylChk >= 20:
            print('Cylinder grip selected !!!')
            targetGrip = cylinderGrip
            set_pwm(0, 0, angle_to_pulse(cylinderGrip[0]))
            time.sleep(1.5)
            break
        if sphereChk >= 20:
            print('Cylinder grip selected !!!')
            targetGrip = sphericalGrip
            break
        if pinchChk >= 20:
            print('Cylinder grip selected !!!')
            targetGrip = pinchGrip
            break

        print(clock.fps(), "fps", end="\n\n")

    return targetGrip


###### Servo Definitions ######

# Constants for I2C and PCA9685
PCA9685_ADDR = 0x40  # I2C address for PCA9685
SERVOMIN = 240     # Minimum pulse length
SERVOMAX = 520    # Maximum pulse length
FREQ = 60            # Servo frequency in Hz

# Initialize I2C
i2c = I2C(1, freq=400000)  # Use I2C bus 1 with a frequency of 400 kHz

# Function to write to a register in the PCA9685
def write_byte(reg, value):
    i2c.writeto_mem(PCA9685_ADDR, reg, bytearray([value]))

# Function to set the PWM frequency
def set_pwm_freq(freq_hz):
    prescale_val = int(25000000.0 / (4096 * freq_hz) - 1)
    write_byte(0x00, 0x10)  # Enter sleep mode
    write_byte(0xFE, prescale_val)  # Set the prescaler value
    write_byte(0x00, 0x00)  # Exit sleep mode
    time.sleep(0.005)
    write_byte(0x00, 0xA1)  # Enable auto-increment

# Function to set PWM for a specific channel (on/off)
def set_pwm(channel, on, off):
    i2c.writeto_mem(PCA9685_ADDR, 0x06 + 4 * channel, bytearray([on & 0xFF, (on >> 8) & 0xFF, off & 0xFF, (off >> 8) & 0xFF]))

# Convert angle to pulse width
def angle_to_pulse(angle):
    pulse = SERVOMAX - (angle * (SERVOMAX - SERVOMIN)) // 180
    return pulse

# Initialize PCA9685
set_pwm_freq(FREQ)


def move_servo_smooth(channel, start_angle, end_angle, step=2, delay=0.01):
    """Move the servo smoothly from start_angle to end_angle in small increments."""
    if start_angle < end_angle:
        step = abs(step)  # Ensure positive step
    else:
        step = -abs(step)  # Ensure negative step

    for angle in range(start_angle, end_angle + step, step):
        pulse = angle_to_pulse(angle)
        set_pwm(channel, 0, pulse)
        time.sleep(delay)  # Small delay to allow movement

def retract_all_fingers(start_angle, end_angle, step=2, delay=0.01):
    if start_angle < end_angle:
        step = abs(step)  # Ensure positive step
    else:
        step = -abs(step)  # Ensure negative step

    for angle in range(start_angle, end_angle + step, step):
        pulse = angle_to_pulse(angle)
        set_pwm(0, 0, pulse)
        set_pwm(1, 0, pulse)
        set_pwm(2, 0, pulse)
        set_pwm(3, 0, pulse)
        set_pwm(4, 0, pulse)
        set_pwm(5, 0, pulse)
        time.sleep(delay)  # Small delay to allow movement

def fist_grip(start_angle, end_angle, step=2, delay=0.01):
    if start_angle < end_angle:
        step = abs(step)  # Ensure positive step
    else:
        step = -abs(step)  # Ensure negative step

    for angle in range(start_angle, end_angle + step, step):
        pulse = angle_to_pulse(180)
        set_pwm(0, 0, pulse)
        set_pwm(1, 0, pulse)
        set_pwm(2, 0, pulse)
        set_pwm(3, 0, pulse)
        set_pwm(4, 0, pulse)
        set_pwm(5, 0, pulse)
        time.sleep(delay)  # Small delay to allow movement

# Grip Options
# Real Order = (0, 1, 2, 3, 4, 5) --> (0, 1, 3, 2, 5, 4)
openGrip = [0, 0, 0, 0, 0, 0]
closedGrip = [180, 180, 180, 180, 180, 180]

powerGripPrimer = [126, 0, 0, 0, 0, 0] # water, gatorade, monster
cylinderGrip = [126, 144, 144, 144, 162, 144] # water, gatorade, monster
sphericalGrip = [144, 115, 115, 115, 130, 125] # apple, mouse
pinchGrip = [99, 135, 115, 105, 0, 0] # Creamer

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
sensor.set_pixformat(sensor.GRAYSCALE)#RGB565)
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

camera_mode = ["off"]

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

##### Servo Functions #####


# Selects the type of grip needed for the detected object
def getGrip(x):
    if x in ['gatorade', 'water', 'monster']:
        runGrip(powerGripPrimer)
        time.sleep(1)
        return cylinderGrip
    elif x == 'mouse':
        return sphericalGrip
    elif x in ['creamer']:
        return pinchGrip
    else:
        return openGrip

def runGrip(grip):
    step = 2
    delay = 0.01
    start_angle = 0
    end_angle = 180
    """Move the servo smoothly from start_angle to end_angle in small increments."""
    if start_angle < end_angle:
        step = abs(step)  # Ensure positive step
    else:
        step = -abs(step)  # Ensure negative step

    for angle in range(start_angle, end_angle + step, step):
        pulse = angle_to_pulse(angle)

        set_pwm(0, 0, angle_to_pulse(grip[0]))
        set_pwm(1, 0, angle_to_pulse(grip[1]))
        set_pwm(2, 0, angle_to_pulse(grip[2]))
        set_pwm(3, 0, angle_to_pulse(grip[3]))
        set_pwm(4, 0, angle_to_pulse(grip[4]))
        set_pwm(5, 0, angle_to_pulse(grip[5]))
        time.sleep(delay)  # Small delay to allow movement

    button_last_state = 1
    while True:
        button_state = button.value()
        if button_state == 1 and button_last_state == 0:
            break
        button_last_state = button_state
        time.sleep(0.05)

    retract_all_fingers(1, 0,step=2, delay=0.1)

##### Camera Function #####

def display_camera_feed():
    lcd.clear()
    camera_mode = ["on"]
    time.sleep(0.5)
    button_last_state = 1
    while camera_mode == ["on"]:
        lcd.write(sensor.snapshot())
        button_state = button.value()
        if button_state == 1 and button_last_state == 0:
            camera_mode = ["off"]
            break
        button_last_state = button_state
        time.sleep(0.05)

# Handle joystick movement and button presses
last_move_time = time.ticks_ms()

retract_all_fingers(1, 0,step=2, delay=0.1)
#time.sleep(2)
#move_servo_smooth(0, 0, 90, step=2, delay=0.01)
#time.sleep(3)

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
    if current_menu == "camera_mode":
        # Display Camera Feed
        #display_camera_feed()
        targetGrip = objectDetection()
        runGrip(targetGrip)
        current_menu = "main_menu"
        menu_stack = ["main_menu"]
        current_index = 0
    elif current_menu == "gripping_screen":
        #fist_grip(0,180,step=2, delay=0.1)
        #time.sleep(2)
        # Display new menu and run grip
        img = image.Image(menu[current_index])
        lcd.write(img, hint=image.SCALE_ASPECT_KEEP)

        # Performs the selected grip
        if 'cyl_menu' in menu_stack:
            print('cyliner grip selected')
            set_pwm(0, 0, angle_to_pulse(cylinderGrip[0]))
            time.sleep(1.5)
            runGrip(cylinderGrip)
            #move_servo_smooth(0, 0, 90, step=2, delay=0.01)
            time.sleep(5)


        if 'sphere_menu' in menu_stack:
            print('sphere grip selected')
            runGrip(sphericalGrip)

        if 'pinch_menu' in menu_stack:
            print('pinch grip selected')
            runGrip(pinchGrip)

        current_menu = "title_screen"
        menu_stack = ["title_screen"]  # Reset menu history
        current_index = 0
        #run_looper()
    else:
        # Display the selected image
        img = image.Image(menu[current_index])
        lcd.write(img, hint=image.SCALE_ASPECT_KEEP)

    time.sleep(0.05)  # Small delay for stability
