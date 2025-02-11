from machine import Pin, ADC

###### Multiplexer Definitions ######

# Setup multiplexer control pins
s0 = Pin('P1', Pin.OUT)  # Replace 'P0' with your actual pin
s1 = Pin('P9', Pin.OUT)
s2 = Pin('P10', Pin.OUT)
s3 = Pin('P11', Pin.OUT)

# Analog pin to read the multiplexer output
adc = ADC(Pin('P6'))
