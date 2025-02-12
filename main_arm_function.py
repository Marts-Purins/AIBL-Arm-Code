import time
import sensor
from LCD_screen_definitions import lcd
from force_sensor_functions import read_force_sensors
from servo_functions import set_servo_position
from button_definitions import button, button_last_state, long_press_duration, enter_deep_sleep

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
