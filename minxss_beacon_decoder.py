import sys
import os
import logging
from ConfigParser import SafeConfigParser
from PySide import QtGui, QtCore
from PySide.QtGui import QMainWindow, QApplication, QColor
from ui_mainWindow import Ui_MainWindow
import connect_port_get_packet
import file_upload
import datetime
from serial.tools import list_ports
import minxss_parser

"""Call the GUI and attach it to functions."""
__author__ = "James Paul Mason"
__contact__ = "jmason86@gmail.com"


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.log = self.createLog()  # Debug log
        self.setupUi(self)
        self.setupAvailablePorts()
        self.assignWidgets()
        self.setupLastUsedSettings()
        self.setupOutputLog()  # Log of buffer data
        self.portReadThread = PortReadThread(self.readPort, self.stopRead)
        QApplication.instance().aboutToQuit.connect(self.prepareToExit)
        self.show()

    def setupAvailablePorts(self):
        """
        Purpose:
            Determine what ports are available for serial reading and populate the combo box with these options
         Input:
           None
         Output:
           None
        """
        self.comboBox_serialPort.clear()
        listPortInfoObjects = list_ports.comports()
        portNames = [x[0] for x in listPortInfoObjects]
        self.comboBox_serialPort.addItems(portNames)

    def assignWidgets(self):
        """
        Purpose:
           Connect UI interactive elements to other functions herein so that code is executed upon user interaction with these elements
         Input:
           None
         Output:
           None
        """
        self.actionConnect.triggered.connect(self.connectClicked)
        self.checkBox_saveLog.stateChanged.connect(self.saveLogToggled)
        self.checkBox_forwardData.stateChanged.connect(self.forwardDataToggled)
        self.checkBox_decodeKiss.stateChanged.connect(self.decodeKissToggled)
        self.actionCompletePass.triggered.connect(self.completePassClicked)

    def setupLastUsedSettings(self):
        """
        Purpose:
           Grab the last used input settings and use those as the startup values
         Input:
           None (though uses the input_properties.cfg configuration file on disk)
         Output:
           None
        """
        parser = SafeConfigParser()
        if os.path.isfile(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg")):
            parser.read(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"))
            self.comboBox_serialPort.insertItem(0, parser.get('input_properties', 'serialPort'))
            self.comboBox_serialPort.setCurrentIndex(0)
            self.lineEdit_baudRate.setText(parser.get('input_properties', 'baudRate'))
            self.lineEdit_ipAddress.setText(parser.get('input_properties', 'ipAddress'))
            self.lineEdit_ipPort.setText(parser.get('input_properties', 'port'))
            self.lineEdit_latitude.setText(parser.get('input_properties', 'latitude'))
            self.lineEdit_longitude.setText(parser.get('input_properties', 'longitude'))
            if parser.get('input_properties', 'decodeKiss') == "True":
                self.checkBox_decodeKiss.setChecked(True)
            else:
                self.checkBox_decodeKiss.setChecked(False)
            if parser.get('input_properties', 'forwardData') == "True":
                self.checkBox_forwardData.setChecked(True)
            else:
                self.checkBox_decodeKiss.setChecked(False)

    def connectClicked(self):
        """
        Purpose:
           Respond to the connect button being clicked -- conect to either the serial or socket as determined by the user/GUI
         Input:
           None (but looks at the current configuration of the GUI for what to connect to and with what settings)
         Output:
           None
        """
        # Write the input settings used to the input_properties.cfg configuration file
        config = SafeConfigParser()
        config.read('input_properties.cfg')
        config.set('input_properties', 'serialPort', self.comboBox_serialPort.currentText())
        config.set('input_properties', 'baudRate', self.lineEdit_baudRate.text())
        config.set('input_properties', 'ipAddress', self.lineEdit_ipAddress.text())
        config.set('input_properties', 'port', self.lineEdit_ipPort.text())
        config.set('input_properties', 'latitude', self.lineEdit_latitude.text())
        config.set('input_properties', 'longitude', self.lineEdit_longitude.text())
        with open(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"), 'wb') as configfile:
            config.write(configfile)

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
                palette.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58))  # Green
                if self.tabWidget_serialIp.currentIndex() == self.tabWidget_serialIp.indexOf(self.serial):
                    self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_serialStatus.setPalette(palette)
                else:
                    self.label_socketStatus.setText(QtGui.QApplication.translate("MainWindow", "Reading", None, QtGui.QApplication.UnicodeUTF8))
                    self.label_socketStatus.setPalette(palette)
            else:
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77))  # Red
                if self.tabWidget_serialIp.currentTabText == "Serial":
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
            palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77))  # Red
            if self.tabWidget_serialIp.currentIndex() == self.tabWidget_serialIp.indexOf(self.serial):
                self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
                self.label_serialStatus.setPalette(palette)
            else:
                self.label_socketStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
                self.label_socketStatus.setPalette(palette)

            # Actually close the port
            self.stopRead()

    def completePassClicked(self):
        """
        Purpose:
            Respond to the complete pass button being clicked -- upload the binary output data, which is handled in a separate function
         Input:
            None
         Output:
            None
        """
        self.uploadData()

    def readPort(self):
        """
        Purpose:
            Read the buffer data from the port (be it serial or socket) in an infinite loop; decode and display any MinXSS housekeeping packets
         Input:
            None
         Output:
            None
        """
        # Infinite loop to read the port and display the data in the GUI and optionally write to output file
        while(True):
            bufferData = self.connectedPort.read_packet()
            if len(bufferData) > 0:
                # Decode KISS escape characters if necessary
                if self.checkBox_decodeKiss.isChecked:
                    bufferData = bufferData.replace(bytearray([0xdb, 0xdc]), bytearray([0xc0]))  # C0 is a special KISS character that get replaced; unreplace it
                    bufferData = bufferData.replace(bytearray([0xdb, 0xdd]), bytearray([0xdd]))  # DB is a special KISS character that get replaced; unreplace it
                formattedBufferData = ' '.join('0x{:02x}'.format(x) for x in bufferData)
                self.textBrowser_serialOutput.append(formattedBufferData)
                self.textBrowser_serialOutput.verticalScrollBar().setValue(self.textBrowser_serialOutput.verticalScrollBar().maximum())

                if self.checkBox_saveLog.isChecked:
                    # Human readable
                    bufferOutputLog = open(self.bufferOutputFilename, 'a', 0)  # append to existing file
                    bufferOutputLog.write(formattedBufferData)
                    bufferOutputLog.closed

                    # Binary
                    bufferOutputBinaryLog = open(self.bufferOutputBinaryFilename, 'a', 0)  # append to existing file
                    bufferOutputBinaryLog.write(bufferData)
                    bufferOutputBinaryLog.closed

                # Parse and interpret the binary data into human readable telemetry
                minxssParser = minxss_parser.Minxss_Parser(bufferData, self.log)
                selectedTelemetryDictionary = minxssParser.parsePacket(bufferData)

                # If valid data, update GUI with telemetry points
                if selectedTelemetryDictionary != -1:
                    ##
                    # Display numbers in GUI
                    ##

                    # Current timestamp
                    self.label_lastPacketTime.setText("Last packet at: {} local, {} UTC".format(datetime.datetime.now().isoformat(), datetime.datetime.utcnow().isoformat()))

                    # Spacecraft State
                    self.label_flightModel.setText("{0:0=1d}".format(selectedTelemetryDictionary['FlightModel']))
                    self.label_commandAcceptCount.setText("{0:0=1d}".format(selectedTelemetryDictionary['CommandAcceptCount']))
                    if selectedTelemetryDictionary['SpacecraftMode'] == 0:
                        self.label_spacecraftMode.setText("Unknown")
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 1:
                        self.label_spacecraftMode.setText("Phoenix")
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 2:
                        self.label_spacecraftMode.setText("Safe")
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 4:
                        self.label_spacecraftMode.setText("Science")
                    if selectedTelemetryDictionary['PointingMode'] == 0:
                        self.label_pointingMode.setText("Coarse Point")
                    elif selectedTelemetryDictionary['PointingMode'] == 1:
                        self.label_pointingMode.setText("Fine Point")
                    if selectedTelemetryDictionary['EnableX123'] == 1:
                        self.label_enableX123.setText("Yes")
                    else:
                        self.label_enableX123.setText("No")
                    if selectedTelemetryDictionary['EnableSps'] == 1:
                        self.label_enableSps.setText("Yes")
                    else:
                        self.label_enableSps.setText("No")
                    if selectedTelemetryDictionary['Eclipse'] == 1:
                        self.label_eclipse.setText("Eclipse")
                    else:
                        self.label_eclipse.setText("In Sun")

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
                    paletteGreen.setColor(QtGui.QPalette.Foreground, QColor(55, 195, 58))  # Green
                    paletteYellow = QtGui.QPalette()
                    paletteYellow.setColor(QtGui.QPalette.Foreground, QColor(244, 212, 66))  # Yellow
                    paletteRed = QtGui.QPalette()
                    paletteRed.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77))  # Red

                    ##
                    # Color code telemetry
                    ##

                    # Spacecraft State
                    if selectedTelemetryDictionary['SpacecraftMode'] == 0:
                        self.label_spacecraftMode.setPalette(paletteRed)
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 1:
                        self.label_spacecraftMode.setPalette(paletteRed)
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 2:
                        self.label_spacecraftMode.setPalette(paletteYellow)
                    elif selectedTelemetryDictionary['SpacecraftMode'] == 4:
                        self.label_spacecraftMode.setPalette(paletteGreen)
                    if selectedTelemetryDictionary['PointingMode'] == 0:
                        self.label_pointingMode.setPalette(paletteYellow)
                    elif selectedTelemetryDictionary['PointingMode'] == 1:
                        self.label_pointingMode.setPalette(paletteGreen)

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
                    if solarPanelMinusYPower >= -1.0 and solarPanelMinusYPower <= 9.7:
                        self.label_solarPanelMinusYPower.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelMinusYPower.setPalette(paletteRed)
                    if solarPanelPlusXPower >= -1.0 and solarPanelPlusXPower <= 5.9:
                        self.label_solarPanelPlusXPower.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusXPower.setPalette(paletteRed)
                    if solarPanelPlusYPower >= -1.0 and solarPanelPlusYPower <= 10.4:
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
                    if selectedTelemetryDictionary['CommBoardTemperature'] >= -8.0 and \
                       selectedTelemetryDictionary['CommBoardTemperature'] <= 60.0:
                        self.label_commBoardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_commBoardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['BatteryTemperature'] >= 5.0 and \
                       selectedTelemetryDictionary['BatteryTemperature'] <= 25:
                        self.label_batteryTemperature.setPalette(paletteGreen)
                    elif selectedTelemetryDictionary['BatteryTemperature'] >= 2.0 and selectedTelemetryDictionary['BatteryTemperature'] < 5.0 or selectedTelemetryDictionary['BatteryTemperature'] > 25.0:
                        self.label_batteryTemperature.setPalette(paletteYellow)
                    else:
                        self.label_batteryTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['EpsBoardTemperature'] >= -8.0 and \
                       selectedTelemetryDictionary['EpsBoardTemperature'] <= 45.0:
                        self.label_epsBoardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_epsBoardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['CdhBoardTemperature'] >= -8.0 and \
                       selectedTelemetryDictionary['CdhBoardTemperature'] <= 29.0:
                        self.label_cdhTemperature.setPalette(paletteGreen)
                    else:
                        self.label_cdhTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['MotherboardTemperature'] >= -13.0 and \
                       selectedTelemetryDictionary['MotherboardTemperature'] <= 28.0:
                        self.label_motherboardTemperature.setPalette(paletteGreen)
                    else:
                        self.label_motherboardTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelMinusYTemperature'] >= -42.0 and \
                       selectedTelemetryDictionary['SolarPanelMinusYTemperature'] <= 61.0:
                        self.label_solarPanelMinusYTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelMinusYTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelPlusXTemperature'] >= -24.0 and \
                       selectedTelemetryDictionary['SolarPanelPlusXTemperature'] <= 65.0:
                        self.label_solarPanelPlusXTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusXTemperature.setPalette(paletteRed)
                    if selectedTelemetryDictionary['SolarPanelPlusYTemperature'] >= -35.0 and \
                       selectedTelemetryDictionary['SolarPanelPlusYTemperature'] <= 58.0:
                        self.label_solarPanelPlusYTemperature.setPalette(paletteGreen)
                    else:
                        self.label_solarPanelPlusYTemperature.setPalette(paletteRed)

    def stopRead(self):
        """
        Purpose:
            Respond to disconnect button being clicked -- disconnect from the port, be it serial or socket
        Input:
            None
        Output:
            None
        """
        self.connectedPort.close()

        # Update GUI
        self.label_serialStatus.setText(QtGui.QApplication.translate("MainWindow", "Port closed", None, QtGui.QApplication.UnicodeUTF8))
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Foreground, QColor(242, 86, 77))  # Red
        self.label_serialStatus.setPalette(palette)

    def saveLogToggled(self):
        """
        Purpose:
            Respond to the user toggling the save log button (create a new output data log as appropriate)
        Input:
            None
        Output:
            Creates a log file on disk if toggling on
        """
        if self.checkBox_saveLog.isChecked():
            self.setupOutputLog()
        else:
            # Update the GUI for the log file - not saving
            self.textBrowser_savingToLogFile.setText("Not saving to log file")
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Text, QColor(242, 86, 77))  # Red
            self.textBrowser_savingToLogFile.setPalette(palette)

    def forwardDataToggled(self):
        """
        Purpose:
           Respond to the user toggling the forward data button (update the GUI to correspond)
        Input:
            None
        Output:
            Creates a log file on disk if toggling on
        """
        if self.checkBox_forwardData.isChecked():
            self.label_uploadStatus.setText("Upload status: Idle")

            # Write the input settings used to the input_properties.cfg configuration file
            config = SafeConfigParser()
            config.read('input_properties.cfg')
            config.set('input_properties', 'forwardData', "True")
            self.log.info("Forward data set to True")
            with open(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"), 'wb') as configfile:
                config.write(configfile)
        else:
            self.label_uploadStatus.setText("Upload status: Disabled")

            # Write the input settings used to the input_properties.cfg configuration file
            config = SafeConfigParser()
            config.read('input_properties.cfg')
            config.set('input_properties', 'forwardData', "False")
            self.log.info("Forward data set to False")
            with open(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"), 'wb') as configfile:
                config.write(configfile)

    def decodeKissToggled(self):
        """
        Purpose:
            Respond to the user toggling the forward data button (update the GUI to correspond)
        Input:
            None
        Output:
            Creates a log file on disk if toggling on
        """
        if self.checkBox_decodeKiss.isChecked():
            config = SafeConfigParser()
            config.read('input_properties.cfg')
            config.set('input_properties', 'decodeKiss', "True")
            self.log.info("Decode KISS set to True")
            with open(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"), 'wb') as configfile:
                config.write(configfile)
        else:
            config = SafeConfigParser()
            config.read('input_properties.cfg')
            config.set('input_properties', 'decodeKiss', "False")
            self.log.info("Decode KISS set to False")
            with open(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "input_properties.cfg"), 'wb') as configfile:
                config.write(configfile)

    def setupOutputLog(self):
        """
        Purpose:
            Create the output files for a human readable hex interpretation of the MinXSS data and a binary file
        Input:
            None
        Output:
            A .tex file with hex MinXSS data and a .dat file with binary MinXSS data
        """
        # Human readable log
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output")):
            os.makedirs(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output"))
        self.bufferOutputFilename = os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output", datetime.datetime.now().isoformat().replace(':', '_')) + ".txt"

        with open(self.bufferOutputFilename, 'w') as bufferOutputLog:
            # Update the GUI for the log file - is saving
            self.textBrowser_savingToLogFile.setText("Saving to log file: " + self.bufferOutputFilename)
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Text, QColor(55, 195, 58))  # Green
            self.textBrowser_savingToLogFile.setPalette(palette)
        bufferOutputLog.closed

        # Binary log
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output")):
            os.makedirs(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output"))
        latitude = self.lineEdit_latitude.text()
        longitude = self.lineEdit_longitude.text()

        self.bufferOutputBinaryFilename = os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "output", datetime.datetime.now().isoformat().replace(':', '_')) + "_" + latitude + "_" + longitude + ".dat"

        with open(self.bufferOutputBinaryFilename, 'w') as bufferOutputBinaryLog:
            self.log.info("Opening binary file for buffer data")
        bufferOutputBinaryLog.closed

    def createLog(self):
        """
        Purpose:
            Initialize a debugger log file
        Input:
            None
        Output:
            The .log file for informational and debug statements
        """
        if not os.path.exists(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log")):
            os.makedirs(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log"))
        log = logging.getLogger('serial_reader_debug')
        handler = logging.FileHandler(os.path.join(os.path.expanduser("~"), "MinXSS_Beacon_Decoder", "log", "minxss_beacon_decoder_debug.log"))
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        log.info("Launched MinXSS Beacon Decoder")
        return log

    def uploadData(self):
        """
        Purpose:
            Upload binary data to the MinXSS team
        Input:
            None (though will grab the .dat binary file from disk)
        Output:
            None (though will send that .dat binary file over the internet via scp to a server handled by the MinXSS team)
        """
        if self.checkBox_forwardData.isChecked:
            self.label_uploadStatus.setText("Upload status: Uploading")
            self.log.info("Uploading data")
            file_upload.upload(self.bufferOutputBinaryFilename, self.log)
            self.label_uploadStatus.setText("Upload status: Complete")
            self.log.info("Upload complete")

    def prepareToExit(self):
        """
        Purpose:
            Respond to the user clicking the close application button -- handle any last business, which is just uploading the binary file in this case
        Input:
            None
        Output:
            None
        """
        self.log.info("About to quit")
        self.uploadData()
        self.log.info("Closing MinXSS Beacon Decoder")


class PortReadThread(QtCore.QThread):
    """
    Purpose:
        Separate class that handles reading the port in an infinite loop -- means the main loop can still be responsive to user interaction
    Input:
        QtCore.QThread: The thread to run this task on
    Output:
        N/A
    """
    def __init__(self, target, slotOnFinished=None):
        super(PortReadThread, self).__init__()
        self.target = target
        if slotOnFinished:
            self.finished.connect(slotOnFinished)

    def run(self, *args, **kwargs):
        """
        Purpose:
            Run a specific block of code in the thread
        Input:
            args, kwargs: flexible input for arguments
        Output:
            None
        """
        self.target(*args, **kwargs)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit(ret)
