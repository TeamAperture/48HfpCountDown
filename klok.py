#!/usr/bin/env python

# Originally created as an idea 
#
# The configuraiton is made with a 74hc595 for each 7-segment display.
# Pinout connections are made the following way:
# Qa - Top led
# Qb - Top right led
# Qc - Bottom right led
# Qd - Bottom led
# Qe - Bottom left led
# Qf - Top left led
# Qg - Middle led
#
# The first 74hc595 is the left of the two hour digits
# The seconde is the right of the two hour digits
# The third is the left of the two minute digits
# The fourth is the right of the two minute digits
# The fifth is the left of the two second digits
# The sixth is the right of the two second digits


import RPi.GPIO as GPIO
import time
import logging

# Set up pins
SD = 18     # Data - Connected to pin 18 of the first 74hc595
SH_CP = 23  # Latch - Connected to pin 23 of all 74hc595s
ST_CP = 24  # Latch - Connected to pin 24 of all 74hc595s

# Segment code from 0 to F in Hexadecimal
#segCode = [0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f,0x77,0x7c,0x39,0x5e,0x79,0x71]

#Running light in Hexadecimal
segCode = [0x01,0x02,0x04,0x08,0x10,0x20,0x40]


def print_msg():
    print 'Program is running...'
    print 'Please press Ctrl+C to end the program...'
   
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SD, GPIO.OUT)
    GPIO.setup(SH_CP, GPIO.OUT)
    GPIO.setup(ST_CP, GPIO.OUT)
    GPIO.output(SD, GPIO.LOW)
    GPIO.output(SH_CP, GPIO.LOW)
    GPIO.output(ST_CP, GPIO.LOW)
       
# Shift the data to 74HC595
def hc595_shift(dat):
    GPIO.output(ST_CP, GPIO.LOW)
    for bit in range(0, 8): 
        GPIO.output(SH_CP, GPIO.LOW)
        GPIO.output(SD, 128 & (dat << bit))
        GPIO.output(SH_CP, GPIO.HIGH)
    GPIO.output(ST_CP, GPIO.HIGH)

def loop():
    while True:
        for i in range(0, len(segCode)):
            hc595_shift(segCode[i])
            time.sleep(0.5)

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
