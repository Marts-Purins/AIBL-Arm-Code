import time, image, display

# Initialize and clear the display
lcd = display.SPIDisplay()
lcd.clear()
time.sleep(1)

# Load an image from the SD card or root directory
img = image.Image("monster.jpg")

# Display the image on the LCD
lcd.write(img, hint=image.SCALE_ASPECT_KEEP)

while True:
    pass  # Keeps the image displayed

