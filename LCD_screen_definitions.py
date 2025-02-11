import sensor
import display

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
