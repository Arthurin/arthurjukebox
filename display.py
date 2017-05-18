#! /usr/bin/env python3
import time

import signal
import sys
import Adafruit_CharLCD as LCD

from enum import Enum

# Raspberry Pi pin configuration:
lcd_rs        = 27  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 22
lcd_d4        = 25
lcd_d5        = 24
lcd_d6        = 23
lcd_d7        = 18
lcd_backlight = 4

# BeagleBone Black configuration:
# lcd_rs        = 'P8_8'
# lcd_en        = 'P8_10'
# lcd_d4        = 'P8_18'
# lcd_d5        = 'P8_16'
# lcd_d6        = 'P8_14'
# lcd_d7        = 'P8_12'
# lcd_backlight = 'P8_7'

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

class Screen(Enum):
	STATUS = 1
	PLAYLISTS = 2

class Display:
	
	def __init__(self):
		self.lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
		                           lcd_columns, lcd_rows, lcd_backlight)		
		self.displayOn = True
		self.screenNumber = Screen.STATUS
		self.state = []
		self.queue = []

	def setState(self,current_state):
		self.state = current_state

	def setQueue(self,current_queue):
		self.queue = current_queue

	def on(self):
		self.screenNumber = Screen.STATUS
		self.lcd.enable_display(True)
		self.lcd.set_backlight(True)
		self.display_screen()

	def off(self):
		self.lcd.set_backlight(0)
		self.lcd.enable_display(0)
		print ("___Turn off___")

	def switch(self):
		self.displayOn = not self.displayOn
		print ("___On/Off___ : {}".format(self.displayOn))
		if(self.displayOn):
			self.screenNumber = Screen.STATUS
			self.on()
		else:
			self.off()

	def next_screen(self):
		if(self.displayOn):
			if self.screenNumber == Screen.STATUS:
				self.screenNumber = Screen.PLAYLISTS
				print ("___Next screen___ : {}".format(self.screenNumber))
			else:
				self.screenNumber = Screen.STATUS
				print ("___Next screen___ : {}".format(self.screenNumber))
			self.display_screen()
		else:
			print("Can't display next screen if turned off ^.^")

	def display_status(self):
		self.lcd.clear()
		line1 = self.state['title']

		if (self.state['status']=='pause'):
			line1 = "|| " + line1
		elif (self.state['status']=='play'):
			line1 = "> " + line1
		else:
			line1 = "_ " + line1
			
		line1 = line1[:16]
		nbTracks = len(self.queue)
		total = sum(int(o['duration']) for o in self.queue)
		m, s = divmod(total, 60)
		h, m = divmod(m, 60)

		if(h>=1):
			total_time = "{2}h{0}m{1}s".format(m,s,h)
		else :
			total_time = "{0}m{1}s".format(m,s)		

		position = 0 if nbTracks==0 else self.state['position']+1
		message = "{0}\n{2}/{1} - {3}".format(line1,nbTracks,position,total_time)
		self.lcd.message(message)
		print(message)

	def display_playlists(self):
		self.lcd.clear()
		self.lcd.message('Display playlistABCDEFGHIJKLMNOPQRSTUVWXYZ')

	def display_screen(self):
		if self.displayOn:
			if self.screenNumber == Screen.STATUS:
				self.display_status()
			else:
				self.display_playlists()

	