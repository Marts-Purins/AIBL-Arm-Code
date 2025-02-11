import time
from machine import I2C
from multiplexer_definitions import s0, s1, s2, s3

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
