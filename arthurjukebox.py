#! /usr/bin/env python3
# https://gist.github.com/ivesdebruycker/4b08bdd5415609ce95e597c1d28e9b9e
# https://volumio.org/forum/gpio-pins-control-volume-t2219.html
# https://pypi.python.org/pypi/socketIO-client
# https://volumio.github.io/docs/API/WebSocket_APIs.html
# Play/pause avec aucun argument (Null) -> play rejouera le dernier morceau mis en pause, mais ne se lancera pas si la liste était vide / player mis sur stop.
from gpiozero import Button
import time
import signal
import subprocess
import os
from socketIO_client import SocketIO, LoggingNamespace
from pprint import pprint
import musics
import random
import pdb
import json
from display import Display
from enum import Enum  

socketIO = SocketIO('localhost', 3000)
queue_uri = []
current_state = None
spawnProcess = None
action_playlist = None
playlist_name = None
display = Display()

def pp_json(json_thing, sort=True, indents=4):
	if type(json_thing) is str:
		return json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents)
	else:
		return json.dumps(json_thing, sort_keys=sort, indent=indents)

class Playlist(Enum):
    PICK_MUSIC = 1
    ADD_MUSIC = 2

class Action(Enum):
	PLAYLIST = 1
	PLAYPAUSENEXT = 2
	PREVIOUSCLEAR = 3
	DISPLAY = 4

class Screen(Enum):
	STATUS = 1
	PLAYLISTS = 2

def next_song(self):
	if(self.shortpress):
		print('next->')
		socketIO.emit('next')
	else: #event already triggered by when_held, reset variable
		self.shortpress = True;

def play_pause(self):
	self.shortpress = False;
	status = current_state['status']
	if status == 'play':
		print ('pause->')
		socketIO.emit('pause','')
	else:
		play()
		

def play():
	status = current_state['status']
	if status == 'pause' or status == 'stop':
		nbTracks = len(queue_uri)
		if (nbTracks == 0):
			#do nothing
			pass
		elif (current_state['position'] >= nbTracks):  # temporary hack (until fixed?) to allow volumio starting back after tracks have been removed
			print ('play->')
			print ('! Hack ! Starting at position (first track is at position 0) {}'.format(nbTracks-1))
			socketIO.emit('play', {"value":0})
			force_reset_position_play = False;
		else:	
			print ('play->')		
			socketIO.emit('play')

def previous(self):	
	if(self.shortpress):
		print ('previous ->')
		socketIO.emit('prev')
		socketIO.emit('getState', '')
	else: #event already triggered by when_held, reset variable
		self.shortpress = True;	

def play_song_from_playlist(self):
	if(self.shortpress):
		print ("Pick and queue random music from playlist : "+self.playlist_name)
		global action_playlist, playlist_name
		action_playlist = Playlist.PICK_MUSIC
		playlist_name = self.playlist_name	
		socketIO.emit("browseLibrary", {"uri":"playlists/"+self.playlist_name})
	else: #event already triggered by when_held, reset variable
		self.shortpress = True;

def clearQueue(self):
	self.shortpress = False;
	print ("Clear queue")
	socketIO.emit('clearQueue',None)

def add_music_to_playlist(self):
	self.shortpress = False;
	global action_playlist, playlist_name
	current_uri = current_state['uri']
	if current_uri != '':	
		action_playlist = Playlist.ADD_MUSIC	
		playlist_name = self.playlist_name
		# TODO check if playlist name exist in PushListPlaylist. Emit listPlaylist to get them
		socketIO.emit("browseLibrary", {"uri": "playlists/"+playlist_name})
	else:
		print ("no song in current state")

def next(self):	
	if(self.shortpress):
		display.next_screen()
	else: #event already triggered by when_held, reset variable
		self.shortpress = True

def switch_on_off(self):
	self.shortpress = False
	display.switch()

class ExtendedButton(Button):
	def __init__(self, pin, myaction, playlist=None):
		Button.__init__(self,pin, hold_time=1)
		self.action = myaction
		self.playlist_name = playlist
		self.shortpress = True;	
		if myaction == Action.PLAYPAUSENEXT:
			# trigger short press
			self.when_released = next_song
			# long press : play/pause
			self.when_held = play_pause
		elif myaction == Action.PLAYLIST:
			socketIO.on('pushBrowseLibrary', on_browse_library) 
			self.when_released = play_song_from_playlist
			self.when_held = add_music_to_playlist
		elif myaction == Action.PREVIOUSCLEAR:
			# trigger short press
			self.when_released = previous
			# long press 
			self.when_held = clearQueue
		elif myaction == Action.DISPLAY:
			# trigger short press
			self.when_released = next
			# long press 
			self.when_held = switch_on_off

# ****************************** SocketIO ******************************

def on_push_queue(args):
	print ("***** Queue has been modified *****")
	#pprint(args)
	global queue_uri
	queue_uri = [o['uri'] for o in args]
	#print (queue_uri)
	display.setQueue(args)
	display.display_screen()
	#print(pp_json(args))
	play()

def on_push_state(*args):
	#print ("* New state event *")
	global current_state
	current_state = args[0]
	display.setState(current_state)
	display.display_screen()
	#print(pp_json(current_state))
	#pprint(args)

def on_event(*args):
	print ("***** EVENT *****")
	pprint(args)

#def on_getState_response(*args):
	#print ("***** pushListPlaylist event ! *****")
	#pprint(args)


def on_browse_library(*args):
	list_view = args[0]['navigation']['lists'][0]['availableListViews'][0]
	if list_view == "list":	
		playlist_items = args[0]['navigation']['lists'][0]['items']
		if action_playlist == Playlist.PICK_MUSIC:
			if not playlist_items: #check if list is empty
				print("List is empty!")
			else:
				array_uri = [o['uri'] for o in playlist_items if o['uri'] not in queue_uri] #list of uri in the array which arent already in queue
				random_uri = random.choice(array_uri)
				socketIO.emit('addToQueue',{"uri": random_uri})

		elif action_playlist == Playlist.ADD_MUSIC:			
			current_song_uri = current_state['uri']
			test = json.dumps(current_song_uri)
			print ("Adding current playing song ("+ test + ") to the playlist : "+playlist_name)
			playlist_uri = [o['uri'] for o in playlist_items]
			if current_song_uri not in playlist_uri:
				socketIO.emit('addToPlaylist', {"name": playlist_name, "service":"mpd", "uri":current_song_uri})
				# !VolumioUI bug : interface not refreshed with the new music if the playlist is displayed
			else:
				print ("Song already in the playlist, no need to add it!")
		else:
			print ("!! Event not supported !!")
	else:
		print ("!-- Event not supported --!")

def lcd():
	global spawnProcess
	print ('LCD')
	cmd = ['sudo', 'python', 'jukebox_lcd.py']
	if spawnProcess is None:
		#spawnProcess = subprocess.Popen("python jukebox_lcd.py", shell=True, preexec_fn=os.setsid)
		spawnProcess = subprocess.Popen(['python', 'jukebox_lcd.py'], preexec_fn=os.setsid)
		print ("lcd started with pid : ", spawnProcess.pid)
	else:
		print ('turn off LCD')
		#sudo kill -TERM -- -10396
		os.killpg(spawnProcess.pid, signal.SIGTERM)
		# ps -ef | grep "python /home/FTP/jukebox_lcd.py" | awk '{print $2}' | xargs sudo kill
		spawnProcess = None


buttonDisplay = ExtendedButton(13,Action.DISPLAY)
#socketIO.on('printConsoleMessage', on_event) #for logs? 
socketIO.on('pushState', on_push_state)
socketIO.on('pushQueue', on_push_queue)
# socketIO.on('pushListPlaylist', on_getState_response) appelé lorsqu'on demande la liste des playlistes au démarrage ou qu'une chanson est ajoutée à la liste. 
# get informations from volumio
socketIO.emit('getState', '')
socketIO.emit('getQueue') # get existing musics in queue  ->  Besoin de ça pour pas ajouter une musique déjà dans la queue (on_browse_library) + Display infos sur la queue
#socketIO.emit('listPlaylist','') # get existing playlists.

# ****************************** Instantiate buttons  ******************************
buttonNEXT_SWITCH = ExtendedButton(19,Action.PLAYPAUSENEXT)
button17 = ExtendedButton(17,Action.PLAYPAUSENEXT)
#button6 = Button(6,hold_time=2) TODO : delete file? copy?
button12 = ExtendedButton(12,Action.PLAYLIST,"Ambiance instru")
button25 = ExtendedButton(26,Action.PLAYLIST,"Calm")
button5 = ExtendedButton(5,Action.PLAYLIST,"Chansons fr")
button6 = ExtendedButton(6,Action.PLAYLIST,"Electro")
button16 = ExtendedButton(16,Action.PLAYLIST,"Soundtracks")

button20 = ExtendedButton(20,Action.PREVIOUSCLEAR)

def signal_term_handler(signal, frame):
	print ("got SIGTERM")
	display.off()
	sys.exit(0)
 
signal.signal(signal.SIGTERM, signal_term_handler)

try:
	socketIO.wait()
except KeyboardInterrupt:
	pass
finally:
	display.off()
	print ('\n Goodbye!')