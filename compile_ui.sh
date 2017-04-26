#!/bin/bash
pyside-uic -o ui_mainWindow.py ui_mainWindow.ui
pyside-rcc -o QtAssets_rc.py assets/QtAssets.qrc 
