# lcd_screen_menu - By: nkf42 - Tue Feb 11 2025

# General idea for code outline

# 1. Import all the necessary functions
# assuming we need all previous functions
# import time
# import sensor
# from LCD_screen_definitions import lcd
# from force_sensor_functions import read_force_sensors
# from servo_functions import set_servo_position
# from button_definitions import button, button_last_state, long_press_duration, enter_deep_sleep

# 2. Define variables needed to characterize five button movement
    # L-R location can characterize scrolling between grip types
    # Up-down location can characterize grip strength - may want to define 0-100% strength
    # Button press can characterize selection

# 3. Import the images (or code the text) used for the display screen
    # 3.1 AIBL Arm Logo
    # 3.2 Manual vs Automatic
    # 3.3 Shapes - Sphere, Cylinder, Pinch Grip
    # 3.4 Grip strength

# 4.

import time, display, image

