import RPi.GPIO as GPIO
import time
import datetime
import os
import sys
import subprocess
from pygame import mixer
import logging
import telegram
from telegram.ext import Updater, CommandHandler

# Telegram-botin token
bot = telegram.Bot(token='528894075:AAHBi4AjhgmSHxFDCVgcN9u9nvjWiALJyF8')
updater = Updater('528894075:AAHBi4AjhgmSHxFDCVgcN9u9nvjWiALJyF8')
dispatcher = updater.dispatcher

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#Defining GPIO pins
TRIG = 23
ECHO = 24
doorBell = 16
openDoor = 12
ringNotifier = 20
unlockedNotifier = 18

#Setting up buttons
GPIO.setup(doorBell,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(openDoor,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#Assigning output pins
GPIO.setup(ringNotifier, GPIO.OUT,)
GPIO.setup(unlockedNotifier,GPIO.OUT)

#Defining door states
initialDoorBellState = False
intitialDoorNotifierState = False

# Funktio, joka ajetaan kun botille lähetetään Telegrammissa komento /avaa
def botResponse(bot, update):
  update.message.reply_text("Door is open!")
  GPIO.output(unlockedNotifier,GPIO.HIGH)
  intitialDoorNotifierState = True
  time.sleep(1)
  GPIO.output(unlockedNotifier,GPIO.LOW)
  intitialDoorNotifierState = False

# Rekisteröidään '/avaa' komento edellämainittuun funktioon
start_handler = CommandHandler('avaa',botResponse)
dispatcher.add_handler(start_handler)
updater.start_polling()

#Door states funktion
#The function notifies that the door bell is ringing
#by flashing the red led light and when answered
#a green led light flashes notifying that
#the door is open
while True:
    #GPIO ports are set input / output
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    
    #Ultrasonic sensor Trig pin is set LOW, for the sensor to settle
    GPIO.output(TRIG, False)
    #Waiting time for Sensor to settle
    time.sleep(2)
    
    #Setting Trig pin of the ultrasonic sensor HIGH
    #for 10 micro seconds and set LOW again
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    #Listenning Ultrasonic sensor's ECHO pin
    #Recording the last LOW state of the ECHO pin
    #just before the return signal is received
    #and the pin goes HIGH
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    
    #When signal is received
    #The pin remains HIGH for the duration
    #of the echo pulse
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
    
    #Recording the duration of the echo pulse
    pulse_duration = pulse_end - pulse_start
    
    #Calculating distance
    #Speed = distance/time(duration of the echo pulse)
    #Speed of sound at sea level 343m/s or 34300cm/s
    #Time is divided by 2 because, the ultrasonic snsor
    #pulse travels the distance from the object and back again
    #(34300/2)=17150
    distance = pulse_duration * 17150
    
    #Rounded to two decimal places
    distance = round(distance, 2)
    
    #Defines the maximum distance to be notified
    if distance < 20:
        print("Movement detected", distance, "cm")
        time.sleep(2)
        bot.sendMessage(chat_id=-302281711,
        text="Movement detected "+ str(distance) + "cm")
    
    # Ovikelloa on painettu
    if GPIO.input(doorBell) == 0:
        print("Door bell is ringing..")
        # Otetaan webkameralla kuva ja asetetaan tiedostonnimeksi aikaleima
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        os.system("fswebcam -S 20 --no-banner "+ timestamp+".jpg")
        # Botti lähettää ryhmään viestin sekä kuvan ovella olijasta
        bot.sendMessage(chat_id=-302281711,
        text="Ovella on joku!")
        bot.send_photo(chat_id=-302281711, photo=open('./'+timestamp+'.jpg', 'rb'))
        #Door is ringing notifier led (RED) goes HIGH and the LOW
        if initialDoorBellState == False:
            GPIO.output(ringNotifier,GPIO.HIGH)
            initialDoorBellState = True
            time.sleep(1)
            GPIO.output(ringNotifier,GPIO.LOW)
            initialDoorBellState = False
    
    #Notifies door state as 'open'
    if GPIO.input(openDoor) == GPIO.LOW:
        print ("Door is open")
        #Door is unlocked notifier led (GREEN) goes HIGH and again LOW
        if intitialDoorNotifierState == GPIO.LOW:
            GPIO.output(unlockedNotifier,GPIO.HIGH)
            intitialDoorNotifierState = True
            time.sleep(1)
            GPIO.output(unlockedNotifier,GPIO.LOW)
            intitialDoorNotifierState = False
    
GPIO.cleanup()    