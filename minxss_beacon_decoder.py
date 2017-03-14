"""Call the GUI and attach it to functions."""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"

import sys
import os
import logging
from PySide.QtGui import *
from PySide.QtCore import *
from ui_mainWindow import Ui_MainWindow
import connect_port_get_packet
from PySide import QtCore, QtGui
import time, datetime
from serial.tools import list_ports
import minxss_parser
import binascii

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setupAvailablePorts()
        self.assignWidgets()
        self.setupOutputLog() # Log of serial data for user
        self.log = self.createLog() # Debug log
        self.portReadThread = PortReadThread(self.readSerial, self.stopRead)
        self.show()
    
    def setupAvailablePorts(self):
        self.comboBox_serialPort.clear()
        listPortInfoObjects = list_ports.comports()
        portNames = [x[0] for x in listPortInfoObjects]
        self.comboBox_serialPort.addItems(portNames)
    
    def assignWidgets(self):
        self.actionConnect.triggered.connect(self.connectClicked)
        self.checkBox_saveLog.stateChanged.connect(self.saveLogToggled)
    
    def connectClicked(self):
        connectButtonText = str(self.actionConnect.iconText())
        if connectButtonText == "Connect":
            self.log.info("Attempting to connect to port")
            
            # Update the GUI to diconnect button
            self.actionConnect.setText(QtGui.QApplication.translate("MainWindow", "Disconnect", None, QtGui.QApplication.UnicodeUTF8))
        
            # Grab the port information from the UI
            if self.tabWidget_serialIp.currentIndex() == self.tabWidget_serialIp.indexOf(self.serial):
                port = self.comboBox_serialPort.currentText()
                baudRate = self.lineEdit_baudRate.text()
            
                # Connect to the serial port and test that it is readable
                connectedPort = connect_port_get_packet.connect_serial(port, baudRate, self.log)
                portReadable = connectedPort.testRead()
            else:
                ipAddress = self.lineEdit_ipAddress.text()
                port = self.lineEdit_ipPort.text()
            
                # Connect to the IP socket but there's no test option so just have to assume its working
                connectedPort = connect_port_get_packet.connect_socket(ipAddress, port, self.log)
                portReadable = 1
        
            # If port is readable, store the reference to it and start reading. Either way, update the GUI serial status
            if portReadable:
                # Store port in instance variable and start reading
                self.connectedPort = connectedPort
                self.portReadThread.start()
                
                # Update GUI
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
                if self.tabWidget_serialIp.currentIndex() == self.tabWidget_serialIp.indexOf(self.serial):
                    self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_serialStatus.setPalette(palette)
                else:
                    self.label_socketStatus.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_socketStatus.setPalette(palette)
            else:
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
                if tabWidget_serialIp.currentTabText == "Serial":
                    self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Read failed", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_serialStatus.setPalette(palette)
                else:
                    self.label_socketStatus.setText(QtGui.QApplication.translate("MainWindow", "Read failed", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_socketStatus.setPalette(palette)
        else:
            self.log.info("Attempting to disconnect from port")
            
            # Update the GUI to connect button
            self.actionConnect.setText(QtGui.QApplication.translate("MainWindow", "Connect", None, QtGui.QApplication.UnicodeUTF8))
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
            if self.tabWidget_serialIp.currentIndex() == self.tabWidget_serialIp.indexOf(self.serial):
                self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
                self.label_serialStatus.setPalette(palette)
            else:
                self.label_socketStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
                self.label_socketStatus.setPalette(palette)

            # Actually close the port
            self.stopRead()
        
    def readSerial(self):
        # Infinite loop to read the port and display the data in the GUI and optionally write to output file
        while(True):
            bufferData = self.connectedPort.read_packet()
            if len(bufferData) > 0:
                formattedBufferData = ' '.join('0x{:02x}'.format(x) for x in bufferData)
                self.textBrowser_serialOutput.append(formattedBufferData)
                self.textBrowser_serialOutput.verticalScrollBar().setValue(self.textBrowser_serialOutput.verticalScrollBar().maximum())
                
                if self.checkBox_saveLog.isChecked:
                    serialOutputLog = open(self.serialOutputFilename, 'a') # append to existing file
                    serialOutputLog.write(formattedBufferData)
                    serialOutputLog.closed

                # Parse and interpret the binary data into human readable telemetry
                minxssParser = minxss_parser.Minxss_Parser(bufferData, self.log)
                selectedTelemetryDictionary = minxssParser.parsePacket(bufferData)
                
                # If valid data, update GUI with telemetry points
                if selectedTelemetryDictionary != -1:
                    ##
                    # Display numbers in GUI
                    ##
                    # Solar Data
                    self.label_spsX.setText("{0:.2f}".format(round(selectedTelemetryDictionary['SpsX'], 2)))
                    self.label_spsY.setText("{0:.2f}".format(round(selectedTelemetryDictionary['SpsY'], 2)))
                    self.label_xp.setText("{0:.2f}".format(round(selectedTelemetryDictionary['Xp'], 2)))
                    
                    # Power
                    self.label_batteryVoltage.setText("{0:.2f}".format(round(selectedTelemetryDictionary['BatteryVoltage'], 2)))
                    if selectedTelemetryDictionary['BatteryChargeCurrent'] > selectedTelemetryDictionary['BatteryDischargeCurrent']:
                        batteryCurrent = selectedTelemetryDictionary['BatteryChargeCurrent'] / 1e3
                        self.label_batteryCurrentText.setText("Battery Charge Current")
                    else:
                        batteryCurrent = selectedTelemetryDictionary['BatteryDischargeCurrent'] / 1e3
                        self.label_batteryCurrentText.setText("Battery Discharge Current")
                    self.label_batteryCurrent.setText("{0:.2f}".format(round(batteryCurrent, 2)))
                    solarPanelMinusYPower = selectedTelemetryDictionary['SolarPanelMinusYVoltage'] * selectedTelemetryDictionary['SolarPanelMinusYCurrent'] / 1e3
                    self.label_solarPanelMinusYPower.setText("{0:.2f}".format(round(solarPanelMinusYPower, 2)))
                    solarPanelPlusXPower = selectedTelemetryDictionary['SolarPanelPlusXVoltage'] * selectedTelemetryDictionary['SolarPanelPlusXCurrent'] / 1e3
                    self.label_solarPanelPlusXPower.setText("{0:.2f}".format(round(solarPanelPlusXPower, 2)))
                    solarPanelPlusYPower = selectedTelemetryDictionary['SolarPanelPlusYVoltage'] * selectedTelemetryDictionary['SolarPanelPlusYCurrent'] / 1e3
                    self.label_solarPanelPlusYPower.setText("{0:.2f}".format(round(solarPanelPlusYPower, 2)))
                    
                    # Temperature
                    self.label_commBoardTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['CommBoardTemperature'], 2)))
                    self.label_batteryTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['BatteryTemperature'], 2)))
                    self.label_epsBoardTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['EpsBoardTemperature'], 2)))
                    self.label_cdhTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['CdhBoardTemperature'], 2)))
                    self.label_motherboardTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['MotherboardTemperature'], 2)))
                    self.label_solarPanelMinusYTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['SolarPanelMinusYTemperature'], 2)))
                    self.label_solarPanelPlusXTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['SolarPanelPlusXTemperature'], 2)))
                    self.label_solarPanelPlusYTemperature.setText("{0:.2f}".format(round(selectedTelemetryDictionary['SolarPanelPlusYTemperature'], 2)))

                    # Setup color palettes
                    paletteGreen = QtGui.QPalette()
                    paletteGreen.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58)) # Green
                    paletteYellow = QtGui.QPalette()
                    paletteYellow.setColor(QtGui.QPalette.Foreground, QColor(244, 212, 66)) # Yellow
                    paletteRed = QtGui.QPalette()
                    paletteRed.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77)) # Red
                    
                    ##
                    # Color code telemetry
                    ##
                    # Solar Data
                    if abs(selectedTelemetryDictionary['SpsX']) <= 3.0:
                        self.label_spsX.setPalette(paletteGreen)
                    else:
                        self.label_spsX.setPalette(paletteRed)
                    if abs(selectedTelemetryDictionary['SpsY']) <= 3.0:
                        self.label_spsY.setPalette(paletteGreen)
                    else:
                        self.label_spsY.setPalette(paletteRed)
                    if selectedTelemetryDictionary['Xp'] <= 24860.0 and selectedTelemetryDictionary['Xp'] >= 0:
                        self.label_xp.setPalette(paletteGreen)
                    else:
                        self.label_xp.setPalette(paletteRed)
                    
                    # Power
                    if solarPanelMinusYPower >= 0 and solarPanelMinusYPower <= 9.7:
                        self.label_solarPanelMinusYPower.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelMinusYPower.setPalette(paletteRed)
                    if solarPanelPlusXPower >= 0 and solarPanelPlusXPower <= 5.9:
                        self.label_solarPanelPlusXPower.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusXPower.setPalette(paletteRed)
                    if solarPanelPlusYPower >= 0 and solarPanelPlusYPower <= 10.4:
                        self.label_solarPanelPlusYPower.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusYPower.setPalette(paletteRed)
                    if selectedTelemetryDictionary['BatteryVoltage'] >= 7.1:
                        self.label_batteryVoltage.setPalette(paletteGreen)
                    elif selectedTelemetryDictionary['BatteryVoltage'] >= 6.9:
                        self.label_batteryVoltage.setPalette(paletteYellow)
                    else:
                        self.label_batteryVoltage.setPalette(paletteRed)
                    if batteryCurrent >= 0 and batteryCurrent <= 2.9:
                        self.label_batteryCurrent.setPalette(paletteGreen)
                    else:
                        self.label_batteryCurrent.setPalette(paletteRed)

                    # Temperature
                    if selectedTelemetryDictionary['CommBoardTemperature'] >= -8.0 and selectedTelemetryDictionary['CommBoardTemperature'] <= 60.0:
                        self.label_commBoardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_commBoardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['BatteryTemperature'] >= 5.0 and selectedTelemetryDictionary['BatteryTemperature'] <= 25:
                        self.label_batteryTemperature.setPalette(paletteGreen)
                    elif selectedTelemetryDictionary['BatteryTemperature'] >= 2.0 and selectedTelemetryDictionary['BatteryTemperature'] < 5.0 or selectedTelemetryDictionary['BatteryTemperature'] > 25.0:
                        self.label_batteryTemperature.setPalette(paletteYellow)
                    else:
                        self.label_batteryTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['EpsBoardTemperature'] >= -8.0 and selectedTelemetryDictionary['EpsBoardTemperature'] <= 45.0:
                        self.label_epsBoardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_epsBoardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['CdhBoardTemperature'] >= -8.0 and selectedTelemetryDictionary['CdhBoardTemperature'] <= 29.0:
                        self.label_cdhTemperature.setPalette(paletteGreen)
                    else:
                        self.label_cdhTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['MotherboardTemperature'] >= -13.0 and selectedTelemetryDictionary['MotherboardTemperature'] <= 28.0:
                        self.label_motherboardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_motherboardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelMinusYTemperature'] >= -42.0 and selectedTelemetryDictionary['SolarPanelMinusYTemperature'] <= 61.0:
                        self.label_solarPanelMinusYTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelMinusYTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelPlusXTemperature'] >= -24.0 and selectedTelemetryDictionary['SolarPanelPlusXTemperature'] <= 65.0:
                        self.label_solarPanelPlusXTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusXTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelPlusYTemperature'] >= -35.0 and selectedTelemetryDictionary['SolarPanelPlusYTemperature'] <= 58.0:
                        self.label_solarPanelPlusYTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusYTemperature.setPalette(paletteRed)

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

class PortReadThread(QtCore.QThread):
    def __init__(self, target, slotOnFinished = None):
        super(PortReadThread, self).__init__()
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
