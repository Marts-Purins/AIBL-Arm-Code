import time
from servo_functions import init_pca9685, set_pwm_frequency, initialize_servos, run_looper

###### EMG Sensor Functions ######

# Moving average function goes here

# Setup
init_pca9685()
set_pwm_frequency(60)  # Set the frequency to 60Hz (standard for servos)

# Servo test (not currently working)
initialize_servos()
time.sleep(1)
run_looper()
