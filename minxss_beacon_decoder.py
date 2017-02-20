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

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.assignWidgets()
        self.setupOutputLog() # Log of serial data for user
        self.log = self.createLog() # Debug log
        self.serialReadThread = SerialReadThread(self.readSerial, self.stopReadClicked)
        self.show()
    
    def assignWidgets(self):
        self.button_connectSerial.clicked.connect(self.connecetSerialClicked)
        self.button_startRead.clicked.connect(self.startReadClicked)
        self.button_stopRead.clicked.connect(self.stopReadClicked)
        self.checkBox_saveLog.stateChanged.connect(self.saveLogToggled)
    
    def connecetSerialClicked(self):
        # Grab the port and baud rate from UI
        port = self.textEdit_serialPort.toPlainText()
        baudRate = self.textEdit_baudRate.toPlainText()
        
        # Connect to the serial port and test that it is readable
        connectedPort = connect_serial_decode_kiss.connect_serial_decode_kiss(port, baudRate, self.log)
        portReadable = connectedPort.testRead()
    
        # If port is readable, store the reference to it and update the GUI
        if portReadable:
            self.connectedPort = connectedPort
            self.label_connected.setText(QtGui.QApplication.translate("MainWindow", "Connected: Yes", None, QtGui.QApplication.UnicodeUTF8))
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
            self.label_connected.setPalette(palette)

    def startReadClicked(self):
        # Update the GUI reading toggle
        self.label_reading.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
        self.label_reading.setPalette(palette)
        
        # Start the dedicated thread reading
        self.serialReadThread.start()
        
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
                    serialOutputLog.write(str(serialData))
                    serialOutputLog.closed

    def stopReadClicked(self):
        # Update the GUI reading toggle
        self.label_reading.setText(QtGui.QApplication.translate("MainWindow", "Not Reading", None, QtGui.QApplication.UnicodeUTF8))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
        self.label_reading.setPalette(palette)

    def saveLogToggled(self):
        if self.checkBox_saveLog.isChecked():
            # Create new log file
            self.serialOutputFilename = 'JPM_serial_reader/output/' + datetime.datetime.now().isoformat() + '.txt'
            with open(self.serialOutputFilename, 'w') as serialOutputLog:
                # Update the GUI for the log file - is saving
                self.label_savingToLogFile.setText("Saving to log file: " + self.serialOutputFilename)
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
                self.label_savingToLogFile.setPalette(palette)
            serialOutputLog.closed
        else:
            # Update the GUI for the log file - not saving
            self.label_savingToLogFile.setText("Not saving to log file")
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
            self.label_savingToLogFile.setPalette(palette)

    def setupOutputLog(self):
        if not os.path.exists("JPM_serial_reader/output"):
            os.makedirs("JPM_serial_reader/output")
        self.serialOutputFilename = "JPM_serial_reader/output/" + datetime.datetime.now().isoformat() + ".txt"
        with open(self.serialOutputFilename, 'w') as serialOutputLog:
            # Update the GUI for the log file - is saving
            self.label_savingToLogFile.setText("Saving to log file: " + self.serialOutputFilename)
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
            self.label_savingToLogFile.setPalette(palette)
        serialOutputLog.closed

    def createLog(self):
        if not os.path.exists("JPM_serial_reader/log"):
            os.makedirs("JPM_serial_reader/log")
        log = logging.getLogger('serial_reader_debug')
        handler = logging.FileHandler('JPM_serial_reader/log/serial_reader_debug.log')
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
    handler = logging.FileHandler('JPM_serial_reader/log/serial_reader_debug.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.info("Launched app")
    
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit( ret )
