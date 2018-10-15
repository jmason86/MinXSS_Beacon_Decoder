# MinXSS_Beacon_Decoder
## Overview
A GUI for decoding serial or socket data received with a UHF HAM radio station from the MinXSS CubeSat in space. There are two MinXSS spacecraft: MinXSS-1 deployed from the International Space Station on 2016 May 16 and operated until 2017 May 06 when it burned up in Earth's atmosphere (as planned); MinXSS-2 will be launched in early 2018. 

MinXSS-1 operates at 437.345 MHz with a beacon every 54 seconds nominally. MinXSS-2 will beacon every 9 seconds at 437.250 MHz. The modulation scheme is GMSK. The beacons contain health and safety information about the spacecraft. 

This program receives the serial or socket data from MinXSS, interprets it, and displays that interpreted data in human readable formats. For example, you can see real time voltages, currents, temperatures, and spacecraft mode. The telemetry is color coded corresponding to the expected ranges for each telemetry point (green = good, yellow = borderline or warning, red = bad). It also forwards the binary data recorded to the MinXSS team (by default, but this can be disabled with the corresponding toggle). 

All of this code is made open source to hopefully encourage other CubeSat programs to adopt it. 

The GUI is built with the designer component of [Qt Creator](https://www.qt.io/download) (open source version; it's not necessary to have this unless you want to edit the interface). It uses the [Qt for Python project](https://www.qt.io/qt-for-python) (pyside2 module, available, e.g., [in anaconda](https://anaconda.org/conda-forge/pyside2)) to convert the Qt Designer .ui file into a .py (this is required if you want to run the code directly but not required if you're running the built beacon decoder application). [minxss_beacon_decoder.py](minxss_beacon_decoder.py) wraps around that GUI code to provide the buttons and text displays with functionality. It uses [connect_port_get_packet.py](connect_port_get_packet.py) to establish a link with the user-specified serial port or TCP/IP socket and then read from it. [minxss_parser.py](minxss_parser.py) is then fed the binary and interprets the data into a dictionary, which is returned to [minxss_beacon_decoder.py](minxss_beacon_decoder.py) for display in the GUI. 

Here is what the layout looks like: 
![Example Screenshot of Telemetry](/screenshots/in_operation1_v2.0.2.png)

The other important component of this program is the optional (but default) automatic forwarding of binary data to the MinXSS team at the University of Colorado at Boulder / Laboratory for Atmospheric and Space Physics. There we merge data received at our own ground stations in Boulder and Alaska, and any other data sent in from volunteer HAM operators around the world. We process the data automatically up to the high-level science products and publish them online at our website (http://lasp.colorado.edu/home/minxss/data/). This all occurs daily. 
In order to forward the data, just make sure to leave the "Forward data" toggle checked, and when the pass is over, either click the "Complete Pass" button or just exit the program. 

![Example Screenshot of Input / Options](/screenshots/in_operation2_v2.0.2.png)

See the release page for periodic releases of code in a good state: https://github.com/jmason86/MinXSS_Beacon_Decoder/releases. 

![Example Screenshot of About](/screenshots/in_operation3_v1.1.0.png)

## How to run from the compiled code (.exe, .app)
1. If you haven't already downloaded [the latest release](https://github.com/jmason86/MinXSS_Beacon_Decoder/releases), do so. 
2. Just double click the downloaded .exe or .app! If it gives you issues, try running it as administrator to give it the permissions to write to your disk. In Windows, you can just right click on the application and select "Run As Administrator". In Mac, open a terminal, change directories to where you have the .app, then change directories into the .app/Contents/MacOS/ and type "sudo MinXSS_Beacon_DecoderMac". 
3. If you're still having problems, make a new directory in your <username> home folder called "MinXSS_Beacon_Decoder". Copy the [input_properties.cfg](input_properties.cfg) file from this MinXSS_Beacon_Decoder codebase into the new folder. Try running again.
4. If it is still not working, create an [issue](https://github.com/jmason86/MinXSS_Beacon_Decoder/issues) on this page. 

## How to run from the code directly
1. If you haven't already downloaded a local copy of this codebase, do so. 
2. Open a terminal, navigate to the directory you are storing this codebase, and type: "python minxss_beacon_decoder". Note that this code was developed with python 3, so it may not work if you're using python 2.
3. That's it! You should see the UI window pop open and you should be able to interact with it. 

## How to edit interface
1. If you don't already have python > anaconda > pyqt installed, do so. In a terminal, type "conda install pyqt".
2. Open the Qt Designer. It should be in a path like this: /Users/<username>/anaconda/bin/Designer.app
3. Go to File > Open and select [ui_mainWindow.ui](ui_mainWindow.ui) from your local copy of this MinXSS_Beacon_Decoder codebase. 
4. Edit away! 
5. Go to File > Save. 
6. Convert the .ui to a .py. To do this, in a Unix terminal, type "./compile_ui.sh" while in the local directory where you have this MinXSS_Beacon_Decoder codebase. If you're on Windows, just take a look at the commands in [compile_ui.sh](compile_ui.sh) and run them in your command prompt. 
7. That's it! Next time you run [minxss_beacon_decoder.py](minxss_beacon_decoder.py), it should show your edits. Note that if you are making edits where you want to change the functionality of the code, you'll need to dive into the corresponding .py files to make those changes as well. 

## How to compile code to executable
1. Get onto the operating system that you want to compile for. The tool we're using (pyinstaller) is not a cross-compiler. That means that if you're on Windows, you can't compile for Mac and vice versa and ditto for Linux. 
2. Test that the code works when you do a normal run from the code directly (see instructions above). 
3. From a terminal window, navigate to the directory where you have your local copy of this codebase. If on Windows, type: "make.bat". If on Mac or Linux, type: "./make.sh". This is just a convenient wrapper script for pyinstaller so you don't have to remember all of the input and output parameters. If it crashes, read the warning messages and respond appropriately. The most likely thing to fail is missing python modules. If that's the reason for failure, in the terminal, just type "pip install" and the name of the module. For example, "pip install pyserial". 

## So you want to modify the code for your own use
1. [Fork the code on github](https://help.github.com/articles/fork-a-repo/).
2. Set up your development environment however you like to interface between your developers local copies and the github server. Or if you don't want to use github, do whatever setup you like. 
3. Edit the code and follow good programming practices with commits, etc. 

### Which code to edit and why
* [QtAssets_rc.py](QtAssets_rc.py): DO NOT EDIT. This code is autogenerated by pyside2 when translating from the Qt Designer [ui_mainWindow.ui](ui_mainWindow.ui) file. That pyside2 call is made in [compile_ui.sh](compile_ui.sh). 
* [compile_ui.sh](compile_ui.sh): You probably don't need to edit this unless you change the names of ui_mainWindow or QtAssets. 
* [connect_port_get_packet.py](connect_port_get_packet.py): You will need to edit this. See the functions read_packet,  findSyncStartIndex, and findSyncStopIndex. Probably the only edits you'll need to make are to replace the syncBytes variable values with your mission's start and stop sync byte patterns, and also the if len(packet) > 500 statement if your packet defintiion is > 500 bytes. 
* [file_upload.py](file_upload.py): You will need to update this. At a minimum, you'll need to change the URL to your server. Our server has a simple PHP script that interacts with [file_upload.py](file_upload.py). Contact James Paul Mason if you want to see what that PHP code looks like. Otherwise, all you need to have is some python code that can upload a file to a server. 
* [input_properties.cfg](input_properties.cfg): If you edit any of the configurable UI elements, you'll need to edit this as well. If you add new configuration options to the UI, you should also capture them in this .cfg file so that they persist for the user. Ditto for removing UI elements. 
* [make.bat](make.bat) and [make.sh](make.sh): You'll need to edit these to use the filenames you want. Everywhere it says "minxss", replace it with whatever your satellite is called. Note that you'll also need to update the filename of [minxss_beacon_decoder.py](minxss_beacon_decoder.py). 
* [minxss_beacon_decoder.py](minxss_beacon_decoder.py): This is the main code. You'll need to edit this to correspond to your own UI elements (i.e., each UI element has to be connected to some code that actually does something). If you've changed the configuration options, you'll need to edit this code to interact with [input_properties.cfg](input_properties.cfg) properly (i.e., consistent variable names, and what those toggles actually do). You'll have to update the variable names for what gets displayed to correspond to what you have in [minxss_parser.py](minxss_parser.py). You'll also need to edit what values are considered green, yellow, or red for each displayed telemetry point. That sounds like a lot of things to edit but it's really not. Most of the code can go unchanged since it is doing pretty basic stuff. 
* [minxss_parser.py](minxss_parser.py): You'll probably need to completely replace this code. You can use it as a template for your own telemetry if you like. But critically, you need to make sure that it returns a dictionary so that [minxss_beacon_decoder.py](minxss_beacon_decoder.py) can still receive what it is expecting. The reason this code needs such heavy editing is that it encapsulates your telemetry definition. For example, MinXSS stores battery voltage in bytes [132:134] and divides by 6415.0 to convert the data numbers to volts. Your telemetry will be different. 
* [ui_mainWindow.py](ui_mainWindow.py): DO NOT EDIT. This code is autogenerated by pyside2 when translating from the Qt Designer [ui_mainWindow.ui](ui_mainWindow.ui) file. That pyside2 call is made in [compile_ui.sh](compile_ui.sh).
* [ui_mainWindow.ui](ui_mainWindow.ui): RECOMMEND NOT EDITING DIRECTLY. This code is autogenerated by the Qt Designer. So if you follow the normal practice of using Qt Designer to edit the GUI using a nice GUI and then save the file, all of the code in the .ui will be replaced. If you make changes to the code directly, then the next time you save the .ui from Qt Designer, those direct code changes will be lost. 
