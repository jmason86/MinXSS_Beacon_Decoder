"""Call the GUI and attach it to functions."""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import sys
import os
import logging
from PySide.QtGui import *
from PySide.QtCore import *
from ui_mainWindow import Ui_MainWindow
import connect_serial_decode_kiss
from PySide import QtCore, QtGui
import time, datetime
from serial.tools import list_ports
import minxss_parser

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setupAvailablePorts()
        self.assignWidgets()
        self.setupOutputLog() # Log of serial data for user
        self.log = self.createLog() # Debug log
        self.serialReadThread = SerialReadThread(self.readSerial, self.stopRead)
        self.show()
    
    def setupAvailablePorts(self):
        self.comboBox_serialPort.clear()
        listPortInfoObjects = list_ports.comports()
        portNames = [x[0] for x in listPortInfoObjects]
        self.comboBox_serialPort.addItems(portNames)
    
    def assignWidgets(self):
        self.actionConnectSerial.triggered.connect(self.connecetSerialClicked)
        self.checkBox_saveLog.stateChanged.connect(self.saveLogToggled)
    
    def connecetSerialClicked(self):
        connectButtonText = str(self.actionConnectSerial.iconText())
        if connectButtonText == "Connect":
            self.log.info("Attempting to connect to serial port")
            
            # Update the GUI to diconnect button
            self.actionConnectSerial.setText(QtGui.QApplication.translate("MainWindow", "Disconnect", None, QtGui.QApplication.UnicodeUTF8))
        
            # Grab the port and baud rate from UI
            port = self.comboBox_serialPort.currentText()
            baudRate = self.lineEdit_baudRate.text()
            
            # Connect to the serial port and test that it is readable
            connectedPort = connect_serial_decode_kiss.connect_serial_decode_kiss(port, baudRate, self.log)
            portReadable = connectedPort.testRead()
        
            # If port is readable, store the reference to it and start reading. Either way, update the GUI serial status
            if portReadable:
                # Store port in instance variable and start reading
                self.connectedPort = connectedPort
                self.serialReadThread.start()
                
                # Update GUI
                self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
                self.label_serialStatus.setPalette(palette)
            else:
                self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Read failed", None, QtGui.QApplication.UnicodeUTF8))
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
                self.label_serialStatus.setPalette(palette)
        else:
            self.log.info("Attempting to disconnect from serial port")
            
            # Update the GUI to connect button
            self.actionConnectSerial.setText(QtGui.QApplication.translate("MainWindow", "Connect", None, QtGui.QApplication.UnicodeUTF8))
            self.stopRead()
        
    def readSerial(self):
        # Infinite loop to read the serial port and display the data in the GUI and optionally write to output file
        while(True):
            serialData = self.connectedPort.read()
            if len(serialData) > 0:
                formattedSerialData = ' '.join(map(lambda x:x.encode('hex'),serialData))
                self.textBrowser_serialOutput.append(formattedSerialData)
                self.textBrowser_serialOutput.verticalScrollBar().setValue(self.textBrowser_serialOutput.verticalScrollBar().maximum())
                
                if self.checkBox_saveLog.isChecked:
                    serialOutputLog = open(self.serialOutputFilename, 'a') # append to existing file
                    serialOutputLog.write(formattedSerialData)
                    serialOutputLog.closed

                # Parse and interpret the binary data into human readable telemetry
                minxssParser = minxss_parser.Minxss_Parser(serialData, self.log)
                print(type(serialData))
                selectedTelemetryDictionary = minxssParser.parsePacket(serialData)
                
                # If valid data, update GUI with telemetry points
                if selectedTelemetryDictionary != -1:
                    self.label_batteryVoltage.setText(str(selectedTelemetryDictionary['BatteryVoltage']))
    
    def stopRead(self):
        self.connectedPort.close()
    
        # Update GUI
        self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
        self.label_serialStatus.setPalette(palette)

    def saveLogToggled(self):
        if self.checkBox_saveLog.isChecked():
            # Create new log file
            self.serialOutputFilename = 'MinXSS_Beacon_Decoder/output/' + datetime.datetime.now().isoformat() + '.txt'
            with open(self.serialOutputFilename, 'w') as serialOutputLog:
                # Update the GUI for the log file - is saving
                self.textBrowser_savingToLogFile.setText("Saving to log file: " + self.serialOutputFilename)
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
                self.textBrowser_savingToLogFile.setPalette(palette)
            serialOutputLog.closed
        else:
            # Update the GUI for the log file - not saving
            self.textBrowser_savingToLogFile.setText("Not saving to log file")
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
            self.textBrowser_savingToLogFile.setPalette(palette)

    def setupOutputLog(self):
        if not os.path.exists("MinXSS_Beacon_Decoder/output"):
            os.makedirs("MinXSS_Beacon_Decoder/output")
        self.serialOutputFilename = "MinXSS_Beacon_Decoder/output/" + datetime.datetime.now().isoformat() + ".txt"
        with open(self.serialOutputFilename, 'w') as serialOutputLog:
            # Update the GUI for the log file - is saving
            self.textBrowser_savingToLogFile.setText("Saving to log file: " + self.serialOutputFilename)
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
            self.textBrowser_savingToLogFile.setPalette(palette)
        serialOutputLog.closed

    def createLog(self):
        if not os.path.exists("MinXSS_Beacon_Decoder/log"):
            os.makedirs("MinXSS_Beacon_Decoder/log")
        log = logging.getLogger('serial_reader_debug')
        handler = logging.FileHandler('MinXSS_Beacon_Decoder/log/minxss_beacon_decoder_debug.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        return log

class SerialReadThread(QtCore.QThread):
    def __init__(self, target, slotOnFinished = None):
        super(SerialReadThread, self).__init__()
        self.target = target
        if slotOnFinished:
            self.finished.connect(slotOnFinished)

    def run(self, *args, **kwargs):
        self.target(*args, **kwargs)

if __name__ == '__main__':
    log = logging.getLogger('serial_reader_debug')
    handler = logging.FileHandler('MinXSS_Beacon_Decoder/log/minxss_beacon_decoder_debug.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.info("Launched app")
    
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit( ret )
