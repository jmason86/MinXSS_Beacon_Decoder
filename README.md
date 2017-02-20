# MinXSS_Beacon_Decoder
A GUI for decoding serial data received with a UHF HAM radio station from the MinXSS CubeSat in space. There are two MinXSS spacecraft: MinXSS-1 deployed from the International Space Station on 2016 May 16 and continues to operate to date; MinXSS-2 will be launched in late 2017. 

MinXSS-1 operates at 437.345 MHz with a beacon every 54 seconds nominally. MinXSS-2 will beacon every 9 seconds at 437.250 MHz. The beacons contain health and safety information about the spacecraft. 

This program receives the serial data from MinXSS, interprets (some of) it, and displays that interpreted data in human readable formats. For example, you can see real time voltages, currents, temperatures, and spacecraft mode. 

All of this code is made open source to hopefully encourage other CubeSat programs to adopt it. 

The GUI is built with Qt Designer (a part of Qt Creator that comes with the anaconda installation of pyqt). It uses pyside (equivalent to PyQt) to convert the Qt Designer .ui file into a .py. minxss_beacon_decoder.py wraps around that GUI code to provide the buttons and text displays with functionality. It uses connect_serial_decode_kiss.py to establish a link with the user-specified serial port and then read from it. minxss_parser.py is then fed the data and interprets the data, which is returne dto minxss_beacon_decoder.py for display in the GUI. 

The other important component of this program is the optional (but default) automatic forwarding of binary data to the MinXSS team at the University of Colorado at Boulder / Laboratory for Atmospheric and Space Physics. There we merge data received at our own ground station, our station being set up in Alaska, and any other data sent in from volunteer HAM operators around the world. We process the data automatically up to the high-level science products and publish them online at our website (http://lasp.colorado.edu/home/minxss/data-ham-radio/science-data/). This all occurs daily. 

More details will be provided in this readme as development progresses. 
