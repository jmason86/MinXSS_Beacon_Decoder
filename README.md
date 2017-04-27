# MinXSS_Beacon_Decoder
A GUI for decoding serial or socket data received with a UHF HAM radio station from the MinXSS CubeSat in space. There are two MinXSS spacecraft: MinXSS-1 deployed from the International Space Station on 2016 May 16 and continues to operate to date; MinXSS-2 will be launched in late 2017. 

MinXSS-1 operates at 437.345 MHz with a beacon every 54 seconds nominally. MinXSS-2 will beacon every 9 seconds at 437.250 MHz. The modulation scheme is GMSK. The beacons contain health and safety information about the spacecraft. 

This program receives the serial or socket data from MinXSS, interprets it, and displays that interpreted data in human readable formats. For example, you can see real time voltages, currents, temperatures, and spacecraft mode. The telemetry is color coded corresponding to the expected ranges for each telemetry point (green = good, yellow = borderline or warning, red = bad). It also forwards the binary data recorded to the MinXSS team (by default, but this can be disabled with the corresponding toggle). 

All of this code is made open source to hopefully encourage other CubeSat programs to adopt it. 

The GUI is built with Qt Designer (a part of Qt Creator that comes with the anaconda installation of pyqt). It uses pyside (equivalent to PyQt) to convert the Qt Designer .ui file into a .py. minxss_beacon_decoder.py wraps around that GUI code to provide the buttons and text displays with functionality. It uses connect_port_get_packet.py to establish a link with the user-specified serial port or TCP/IP socket and then read from it. minxss_parser.py is then fed the binary and interprets the data into a dictionary, which is returned to minxss_beacon_decoder.py for display in the GUI. 

Here is what version 3 of the layout looks like: 
![Example Screenshot of Telemetry](/screenshots/in_operation1v1.1.0.png)

The other important component of this program is the optional (but default) automatic forwarding of binary data to the MinXSS team at the University of Colorado at Boulder / Laboratory for Atmospheric and Space Physics. There we merge data received at our own ground stations in Boulder and Alaska, and any other data sent in from volunteer HAM operators around the world. We process the data automatically up to the high-level science products and publish them online at our website (http://lasp.colorado.edu/home/minxss/data-ham-radio/science-data/). This all occurs daily. 
In order to forward the data, just make sure to leave the "Forward data" toggle checked, and when the pass is over, either click the "Complete Pass" button or just exit the program. 

![Example Screenshot of Input / Options](/screenshots/in_operation2v1.1.0.png)

See the release page for periodic releases of code in a good state: https://github.com/jmason86/MinXSS_Beacon_Decoder/releases and some helpful tips in the release notes from K4KDR for getting it to work with Windows. The specific points made there are things that will be improved in the decoder with the end-goal of making the user experience as seemless as possible. 

![Example Screenshot of About](/screenshots/in_operation3v1.1.0.png)

More details will be provided in this readme as development progresses. 
