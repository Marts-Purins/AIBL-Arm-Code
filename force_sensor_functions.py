import time
from multiplexer_definitions import adc
from servo_functions import select_channel

###### Force Sensor Functions ######

# Read force sensor values
def read_force_sensors(num_sensors):
    readings = []
    for i in range(num_sensors):
        select_channel(i)  # Select the channel
        time.sleep_ms(5)  # Allow some time for the signal to stabilize
        readings.append(adc.read_u16())  # Read the analog value
    return readings
