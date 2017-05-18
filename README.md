# arthurjukebox
Manage music library easily by making a music-box. I'm using Volumio, Raspberry and its gpio (Buttons, LCD screen)

## Install
sudo apt-get install git-core  
git clone https://github.com/Arthurin/arthurjukebox.git
sudo apt-get install python3  
sudo apt-get install python3-pip  
sudo pip3 install RPi.GPIO  
sudo pip3 install gpiozero  
sudo pip3 install -U socketIO-client  
sudo python3 ~/arthurjukebox/Adafruit_Python_CharLCD/setup.py install  
sudo python3 ~/arthurjukebox/arthurjukebox.py  

## Dev
You can install rsub for Sublime Text https://wrgms.com/editing-files-remotely-via-ssh-on-sublimetext-3/  
sudo apt-get install tmux  

### Settings
Python 3.4.2  
Volumio Version: 2.175 Release date: 16-05-2017  
Raspbian GNU/Linux 8 (jessie)  