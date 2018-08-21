#!/usr/bin/env python

# Originally created as an idea 
#
# The configuration is made with a 74hc595 for each 7-segment display.
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
# The second is the right of the two hour digits
# The third is the left of the two minute digits
# The fourth is the right of the two minute digits
# The fifth is the left of the two second digits
# The sixth is the right of the two second digits


import RPi.GPIO as GPIO
from pathlib import Path
from datetime import datetime, timedelta
import math
import logging

# Set up pins
SD = 18     # Data - Connected to pin 18 of the first 74hc595
SH_CP = 23  # Latch - Connected to pin 23 of all 74hc595s
ST_CP = 24  # Latch - Connected to pin 24 of all 74hc595s

# Segment code from 0 to F in Hexadecimal
#segCode = [0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f,0x77,0x7c,0x39,0x5e,0x79,0x71]

# Running light in Hexadecimal
#segCode = [0x01,0x02,0x04,0x08,0x10,0x20,0x40]

# Digits 0-9, aligned to bits 0-6
#segCode = [0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f]

segDict = {'0': 0x7e,
           '1': 0x0c,
           '2': 0xb6,
           '3': 0x9e,
           '4': 0xcc,
           '5': 0xda,
           '6': 0xfa,
           '7': 0x0e,
           '8': 0xfe,
           '9': 0xde,
           'H': 0xec,
           'F': 0xe2,
           'P': 0xe6,
           ' ': 0x00}
noSegCode = 0x80
nShiftBits = 48
zeroTimeout = 3600 #time in seconds after which clock will show '48 HFP' again

class State:
    clockPaused = True
    clockFinish = datetime.now()
    currentCountdown = timedelta(seconds = -zeroTimeout)

def print_msg():
    print('Program is running...')
    print('Please press Ctrl+C to end the program...')
   
def setup(state):
    initClock(state)
    initGPIO()
    setClock(state)

def initGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SD, GPIO.OUT)
    GPIO.setup(SH_CP, GPIO.OUT)
    GPIO.setup(ST_CP, GPIO.OUT)
    GPIO.output(SD, GPIO.LOW)
    GPIO.output(SH_CP, GPIO.LOW)
    GPIO.output(ST_CP, GPIO.LOW)

def initClock(state):
    timePath = Path("clock.48h")
    if timePath.is_file():

        timeFile = open(timePath.resolve(), 'r')
        timeStr = timeFile.read()
        timeFile.close()

        state.clockPaused = False
        state.clockFinish = datetime.strptime(timeStr, "%Y/%m/%d - %H:%M:%S")
        state.currentCountdown = state.clockFinish - datetime.now()

#Shift the data to 74HC595
def hc595_shift(dat, bits):
    leftBit = 1 << (bits - 1)

    GPIO.output(ST_CP, GPIO.LOW)
    for bit in range(0, bits):
        GPIO.output(SH_CP, GPIO.LOW)
        GPIO.output(SD, leftBit & (dat << bit))
        GPIO.output(SH_CP, GPIO.HIGH)
    GPIO.output(ST_CP, GPIO.HIGH)

def loop(state):
    while True:
        if not state.clockPaused:
            state.currentCountdown = state.clockFinish - datetime.now()
            if math.ceil(state.currentCountdown.total_seconds()) < -zeroTimeout:
                state.clockPaused = True
                state.currentCountdown = timedelta(seconds = -zeroTimeout)

            setClock(state)

def setClock(state):
    total_seconds = math.ceil(state.currentCountdown.total_seconds())

    if total_seconds > 0:
        hours = int(total_seconds / 3600)
        minutes = int((total_seconds % 3600) / 60)
        seconds = int(total_seconds % 60)

        segCode = str2segCode('{:02d}{:02d}{:02d}'.format(hours, minutes, seconds))
        #print('{:02d}{:02d}{:02d}'.format(hours, minutes, seconds) + " - " + '{:#018x}'.format(segCode))
        hc595_shift(segCode, nShiftBits)
    elif total_seconds <= 0 and total_seconds > -zeroTimeout:
        on = int(state.currentCountdown.total_seconds() * 2) % 2 == 0
        if on:
            segCode = str2segCode('000000')
        else:
            segCode = str2segCode('      ')
        #print('000000' + " - " + '{:#018x}'.format(segCode))
        hc595_shift(segCode, nShiftBits)
    else:
        segCode = str2segCode('48 HFP')
        #print('48 HFP' + " - " + '{:#018x}'.format(segCode))
        hc595_shift(segCode, nShiftBits)

def str2segCode(str):
    segCode = 0x0000000000000000
    for c in reversed(str):
        segCode = (segCode << 8) | getSegCode(c)
    return segCode

def getSegCode(c):
    return segDict.get(c, noSegCode)

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    print_msg()

    state = State()

    setup(state)
    try:
        loop(state)
    except KeyboardInterrupt:
        destroy()