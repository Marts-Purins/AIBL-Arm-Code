from machine import Pin, ADC, I2C
import time

global sensor_values # global allows its use in every function
sensor_values = [0,0,0,0,0,0]

# Setup multiplexer control pins
s0 = Pin('P1', Pin.OUT)  # Replace 'P0' with your actual pin
s1 = Pin('P9', Pin.OUT)
s2 = Pin('P10', Pin.OUT)
s3 = Pin('P11', Pin.OUT)

# Analog pin to read the multiplexer output
adc = ADC(Pin('P6'))  # Replace 'P6' with the analog pin you're using

# Function to select a channel on the multiplexer
def select_channel(channel):
    # Convert channel number to binary and set pins accordingly
    s0.value((channel >> 0) & 1)
    s1.value((channel >> 1) & 1)
    s2.value((channel >> 2) & 1)
    s3.value((channel >> 3) & 1)

# Read force sensor values
def read_force_sensors(num_sensors):
    readings = []
    for i in range(num_sensors):
        select_channel(i)  # Select the channel
        time.sleep_ms(5)  # Allow some time for the signal to stabilize
        readings.append(adc.read_u16())  # Read the analog value
    return readings


# Constants for I2C and PCA9685
PCA9685_ADDR = 0x40  # I2C address for PCA9685
SERVOMIN = 270     # Minimum pulse length
SERVOMAX = 520    # Maximum pulse length
FREQ = 60            # Servo frequency in Hz

# Initialize I2C (RT1062 board with OpenMV)
#i2c = I2C(1, scl=Pin('P5'), sda=Pin('P4'), freq=400000)  # I2C bus 1, frequency 400kHz

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
        sensor_values = read_force_sensors(6)
        print("Force Sensor Values:", sensor_values)
        if sensor_values[0] < 3000:
            pulse = angle_to_pulse(angle)
            set_pwm(channel, 0, pulse)
            time.sleep(delay)  # Small delay to allow movement
        else:
            break

def retract_all_fingers(start_angle, end_angle, step=2, delay=0.01):
    if start_angle < end_angle:
        step = abs(step)  # Ensure positive step
    else:
        step = -abs(step)  # Ensure negative step

    for angle in range(start_angle, end_angle + step, step):
        sensor_values = read_force_sensors(6)
        print("Force Sensor Values:", sensor_values)
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
        sensor_values = read_force_sensors(6)
        print("Force Sensor Values:", sensor_values)
        pulse = angle_to_pulse(180)
        set_pwm(0, 0, pulse)
        set_pwm(1, 0, pulse)
        set_pwm(2, 0, pulse)
        set_pwm(3, 0, pulse)
        set_pwm(4, 0, pulse)
        set_pwm(5, 0, pulse)
        time.sleep(delay)  # Small delay to allow movement

#move_servo_smooth(0, 0, 180, step=5, delay=0.02)  # 5° increments with 20ms delay
#time.sleep(2)

retract_all_fingers(1,0,step=2, delay=0.1)
time.sleep(2)


while True:
    fist_grip(0,180,step=2, delay=0.1)
    time.sleep(2)
    retract_all_fingers(1,0,step=2, delay=0.1)
    time.sleep(15)
