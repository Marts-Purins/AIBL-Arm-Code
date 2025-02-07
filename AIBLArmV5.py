import time
import machine
import sensor
import display
from machine import Pin, I2C, ADC

###### LCD Screen Definitions ######

sensor.reset()  # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565)  # or sensor.GRAYSCALE
sensor.set_framesize(sensor.QQVGA2)  # Special 128x160 framesize for LCD Shield.
# Initialize the lcd screen.
# Note: A DAC or a PWM backlight controller can be used to control the
# backlight intensity if supported:
#  lcd = display.SPIDisplay(backlight=display.DACBacklight(channel=2))
#  lcd.backlight(25) # 25% intensity
# Otherwise the default GPIO (on/off) controller is used.
lcd = display.SPIDisplay()

###### 5D Button Definitions ######

# Setup the button for wake-up
button = Pin('P13', Pin.IN, Pin.PULL_UP)  # Button connected to GPIO 5

# Debounce variables
button_last_state = 1
button_press_time = 0
long_press_duration = 5000  # 5 seconds (in ms)

# Test Number 1000

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



###### Servo Definitions ######

# Initialize I2C bus for PCA9685 communication
i2c = I2C(1, freq=400000)

# PCA9685 address
PCA9685_ADDR = 0x40  # Default I2C address of the PCA9685

# PCA9685 Registers
MODE1 = 0x00
PRE_SCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09

# Servo range
servo_min = 240  # Minimum pulse length
servo_max = 530  # Maximum pulse length



###### Multiplexer Definitions ######

# Setup multiplexer control pins
s0 = Pin('P1', Pin.OUT)  # Replace 'P0' with your actual pin
s1 = Pin('P9', Pin.OUT)
s2 = Pin('P10', Pin.OUT)
s3 = Pin('P11', Pin.OUT)

# Analog pin to read the multiplexer output
adc = ADC(Pin('P6'))



###### Servo Functions ######

# Function to write a byte to a register on PCA9685
def write_byte(register, value):
    i2c.writeto(PCA9685_ADDR, bytearray([register, value]))

# Function to read a byte from a register on PCA9685
def read_byte(register):
    return i2c.readfrom_mem(PCA9685_ADDR, register, 1)[0]

# Initialize PCA9685 (set to normal mode)
def init_pca9685():
    # Wake up the PCA9685 from sleep mode
    write_byte(MODE1, 0x00)  # Clear sleep mode
    time.sleep(0.1)  # Wait for the mode change

# Set PWM frequency for the PCA9685
def set_pwm_frequency(freq):
    prescale_value = int(25000000.0 / (4096.0 * freq) - 1)
    write_byte(PRE_SCALE, prescale_value)
    write_byte(MODE1, 0x80)  # Restart the chip

# Set the position of a servo (0-100%)
def set_servo_position(channel, position):
    pulse_width = servo_min + (position * (servo_max - servo_min) // 100)
    on_time = 0
    off_time = pulse_width
    write_byte(LED0_ON_L + 4 * channel, on_time & 0xFF)
    write_byte(LED0_ON_H + 4 * channel, on_time >> 8)
    write_byte(LED0_OFF_L + 4 * channel, off_time & 0xFF)
    write_byte(LED0_OFF_H + 4 * channel, off_time >> 8)

# Initialize all servos
def initialize_servos():
    for i in range(6):
        set_servo_position(i, 100)  # Start all servos in retracted position

# Deactivate a servo by setting its PWM signal to zero
def deactivate_servo(channel):
    # Stops the servo where it is
    write_byte(LED0_ON_L + 4 * channel, 0x00)  # Turn off ON register
    write_byte(LED0_ON_H + 4 * channel, 0x00)
    write_byte(LED0_OFF_L + 4 * channel, 0x00)  # Turn off OFF register
    write_byte(LED0_OFF_H + 4 * channel, 0x00)

    # Keeps servo activated when stopped
    set_servo_position(channel, 0)


# Main control loop
def run_looper():
    # Retract all servos
    for i in range(6):
        set_servo_position(i, 0)
    time.sleep(3)

    # Extend all servos
    for i in range(6):
        set_servo_position(i, 100)
    time.sleep(3)

# Function to select a channel on the multiplexer
def select_channel(channel):
    # Convert channel number to binary and set pins accordingly
    s0.value((channel >> 0) & 1)
    s1.value((channel >> 1) & 1)
    s2.value((channel >> 2) & 1)
    s3.value((channel >> 3) & 1)



###### Force Sensor Functions ######

# Read force sensor values
def read_force_sensors(num_sensors):
    readings = []
    for i in range(num_sensors):
        select_channel(i)  # Select the channel
        time.sleep_ms(5)  # Allow some time for the signal to stabilize
        readings.append(adc.read_u16())  # Read the analog value
    return readings

###### EMG Sensor Functions ######

# Moving average function goes here

# Setup
init_pca9685()
set_pwm_frequency(60)  # Set the frequency to 60Hz (standard for servos)

# Servo test (not currently working)
initialize_servos()
time.sleep(1)
run_looper()


sensor_values = [0, 0, 0, 0, 0, 0, 0, 0, 0]

while True:
    lcd.write(sensor.snapshot())  # Take a picture and display the image.

    # Takes in all ADC data from MUX
    sensor_values = read_force_sensors(9)  # Read values from 6 sensors
    sensor_values[6] = int((sensor_values[6] / 65536) * 100) # Percent of button x-axis
    sensor_values[7] = int((sensor_values[7] / 65536) * 100) # Percent of button y-axis
    print("Sensor Values:", sensor_values)

    ## Force Sensor Opertaions ##

    if sensor_values[0] < 6000:
        #continue
        set_servo_position(2, 10)

    ## 5D Button Operations ##

    if button.value() == 0:  # Button is pressed
        if button_last_state == 1:  # First time detecting the press
            button_press_time = time.ticks_ms()

        # Check for long press
        if time.ticks_diff(time.ticks_ms(), button_press_time) >= long_press_duration:
            print("Button held for 5 seconds. Turning off...")
            enter_deep_sleep()
            break  # Stop the main loop

    else:  # Button is not pressed
        if button_last_state == 0:  # Button was released
            if time.ticks_diff(time.ticks_ms(), button_press_time) < long_press_duration:
                print("Short press detected. Device stays on.")

        button_press_time = 0  # Reset press time

    button_last_state = button.value()
    #time.sleep(0.1)  # Debounce delay

    time.sleep(0.03)  # Delay to allow for processing
