# Serial_Reader_Pyside_Qt
Simple serial port reader using python, pyside, and Qt Designer

To run, simply do: 
python serial_reader.py 

This should open up the GUI. Specify the your port of interest and a baud rate then click connect. 
In the output panel, the connected indicator should turn green. Click the start read button and once you start streaming data into the serial port, it should show up in the output panel. It will also output to a log file as indicated unless you uncheck the save log checkbox. 

![Alt text](/screenshots/Screenshot 2017-02-13 18.35.34.png?raw=true "Example Screenshot")

To edit the .ui file, you should use Qt Designer (comes with anaconda) or Qt Creator (comes with install of Qt). 
To convert the .ui to the .py, do: 
pyside-uic -x ui_mainWindow.ui -o ui_mainWindow.py
or
pyuic -x ui_mainWindow.ui -o ui_mainWindow.py
(or pyuic4 or pyuic5, whatever you have). 
You should never manually edit the code in the .ui or corresponding .py because it will be overwritten when you edit with Qt Designer/Creator. 

The Xcode project here is just a convenience to organize the .py files. You can edit the .py files in any text editor or IDE of your choosing. 
