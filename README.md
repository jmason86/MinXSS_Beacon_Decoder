# MinXSS_Beacon_Decoder
A GUI for decoding serial data received with a UHF HAM radio station from the MinXSS CubeSat in space. There are two MinXSS spacecraft: MinXSS-1 deployed from the International Space Station on 2016 May 16 and continues to operate to date; MinXSS-2 will be launched in late 2017. 

MinXSS-1 operates at 437.345 MHz with a beacon every 54 seconds nominally. MinXSS-2 will beacon every 9 seconds at 437.250 MHz. The modulation scheme is GMSK. The beacons contain health and safety information about the spacecraft. 

This program receives the serial data from MinXSS, interprets (some of) it, and displays that interpreted data in human readable formats. For example, you can see real time voltages, currents, temperatures, and spacecraft mode. 

All of this code is made open source to hopefully encourage other CubeSat programs to adopt it. 

The GUI is built with Qt Designer (a part of Qt Creator that comes with the anaconda installation of pyqt). It uses pyside (equivalent to PyQt) to convert the Qt Designer .ui file into a .py. minxss_beacon_decoder.py wraps around that GUI code to provide the buttons and text displays with functionality. It uses connect_serial_decode_kiss.py to establish a link with the user-specified serial port and then read from it. minxss_parser.py is then fed the data and interprets the data, which is returne dto minxss_beacon_decoder.py for display in the GUI. 

Here is what version 2 of the layout looks like: 
![Alt text](/screenshots/Layout_v2.png?raw=true "Example Screenshot")

The other important component of this program is the optional (but default) automatic forwarding of binary data to the MinXSS team at the University of Colorado at Boulder / Laboratory for Atmospheric and Space Physics. There we merge data received at our own ground station, our station being set up in Alaska, and any other data sent in from volunteer HAM operators around the world. We process the data automatically up to the high-level science products and publish them online at our website (http://lasp.colorado.edu/home/minxss/data-ham-radio/science-data/). This all occurs daily. 

See the release page for periodic releases of code in a good state: https://github.com/jmason86/MinXSS_Beacon_Decoder/releases and some helpful tips in the release notes from K4KDR for getting it to work with Windows. The specific points made there are things that will be improved in the decoder with the end-goal of making the user experience as seemless as possible. 

The executable files are now too large (>100 MB) to store on github. You can get them here:
[Mac](https://www.dropbox.com/sh/emswiioananxqiz/AAB56jSNaOtN7YQwasMT_3BRa?dl=0), 
[Windows](https://www.dropbox.com/s/uqafljvdrjdqzpt/MinXSS_Beacon_DecoderWin.exe?dl=0)

More details will be provided in this readme as development progresses. 
