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

from machine import Pin, ADC, SPI
import st7735
import time
import vga1_16x16 as font  # Import font file (install fonts if needed)

# SPI Configuration for ST7735
spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
tft = st7735.ST7735(spi, cs=Pin(5), dc=Pin(2), rst=Pin(4), width=128, height=160)

# Joystick Setup
joy_x = ADC(Pin(34))  # X-axis
joy_y = ADC(Pin(35))  # Y-axis
joy_button = Pin(32, Pin.IN, Pin.PULL_UP)  # Button (0 = pressed)

# Menu items
menu_items = ["Sphere", "Cylinder", "Pinch"]
selected_index = 0

# Colors (RGB565 format)
WHITE = st7735.color565(255, 255, 255)
BLACK = st7735.color565(0, 0, 0)
RED = st7735.color565(255, 0, 0)
GREEN = st7735.color565(0, 255, 0)
BLUE = st7735.color565(0, 0, 255)

# Function to display the menu
def display_menu():
    tft.fill(BLACK)  # Clear screen
    for i, item in enumerate(menu_items):
        color = RED if i == selected_index else WHITE
        tft.text(font, f"> {item}" if i == selected_index else f"  {item}", 10, i * 20, color)
    tft.show()

display_menu()

while True:
    x = joy_x.read()
    y = joy_y.read()
    btn = joy_button.value()  # 0 = pressed

    # Move down
    if y > 3000:
        selected_index = (selected_index + 1) % len(menu_items)
        display_menu()
        time.sleep(0.2)

    # Move up
    elif y < 1000:
        selected_index = (selected_index - 1) % len(menu_items)
        display_menu()
        time.sleep(0.2)

    # Confirm selection
    if btn == 0:
        tft.fill(BLACK)
        tft.text(font, "Selected:", 10, 60, GREEN)
        tft.text(font, menu_items[selected_index], 10, 80, GREEN)
        tft.show()
        time.sleep(1)
        display_menu()
