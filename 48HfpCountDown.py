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
#from pathlib import Path
from datetime import datetime, timedelta
import math
import logging
import os.path

# Set up pins
SD = 16     # Data - Connected to pin 16 of the first 74hc595
SH_CP = 20  # Latch - Connected to pin 20 of all 74hc595s
ST_CP = 21  # Latch - Connected to pin 21 of all 74hc595s
START_BUTTON = 12

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

#countdownTime = timedelta(hours = 48, minutes = 30, seconds = 0)
countdownTime = timedelta(hours = 0, minutes = 0, seconds = 5)

class State:
    clockFinish = datetime.now()
    currentCountdown = timedelta(seconds = -zeroTimeout)
    clockPaused = True
    last_start_button_state = False

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

    GPIO.setup(START_BUTTON, GPIO.IN)

def initClock(state):
    timePath = 'clock.48h'
    
    if os.path.isfile(timePath):
        timeFile = open(timePath, 'r')
        timeStr = timeFile.read()
        timeFile.close()

        state.clockFinish = datetime.strptime(timeStr, "%Y/%m/%d - %H:%M:%S")
        state.currentCountdown = state.clockFinish - datetime.now()
        state.clockPaused = False

        print('finish time loaded: ' + datetime.strftime(state.clockFinish, "%Y/%m/%d - %H:%M:%S"))

#Shift the data to 74HC595
def hc595_shift(dat, bits):
    #str = ''
    leftBit = 1 << (bits - 1)

    GPIO.output(ST_CP, GPIO.LOW)
    for bit in range(0, bits):
        GPIO.output(SH_CP, GPIO.LOW)
        #if (leftBit & (dat << bit)) > 0:
        #    str = str + '1'
        #else:
        #    str = str + '0'
        GPIO.output(SD, GPIO.HIGH if (leftBit & (dat << bit)) > 0 else GPIO.LOW)
        GPIO.output(SH_CP, GPIO.HIGH)
    #print str
    GPIO.output(ST_CP, GPIO.HIGH)

def loop(state):
    while True:
        if not state.clockPaused:
            state.currentCountdown = state.clockFinish - datetime.now()
            if math.ceil(state.currentCountdown.total_seconds()) < -zeroTimeout:
                state.clockPaused = True
                state.currentCountdown = timedelta(seconds = -zeroTimeout)

            setClock(state)

        if start_button_pressed(state):
            startClock(state)


def start_button_pressed(state):
    button_pressed = GPIO.input(START_BUTTON)
    #print button_pressed
    if button_pressed and not state.last_start_button_state:
        startClock(state)

    state.last_start_button_state = button_pressed


def startClock(state):
    state.clockFinish = datetime.now() + countdownTime
    state.currentCountdown = state.clockFinish - datetime.now()
    state.clockPaused = False
    
    timePath = 'clock.48h'
    timeFile = open(timePath, 'w+')
    timeStr = datetime.strftime(state.clockFinish, "%Y/%m/%d - %H:%M:%S")
    timeFile.write(timeStr)
    timeFile.close()

    print('started countdown to: ' + datetime.strftime(state.clockFinish, "%Y/%m/%d - %H:%M:%S"))


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
        #sprint('000000' + " - " + '{:#018x}'.format(segCode))
        hc595_shift(segCode, nShiftBits)
    else:
        segCode = str2segCode('48 HFP')
        #print('48 HFP' + " - " + '{:#018x}'.format(segCode))
        hc595_shift(segCode, nShiftBits)


def str2segCode(str):
    segCode = 0x0000000000000000
    #for c in reversed(str):
    for c in str:
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