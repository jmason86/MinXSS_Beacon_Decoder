#!/bin/bash
pyside2-uic -o ui_mainWindow.py ui_mainWindow.ui
pyside2-rcc -o QtAssets_rc.py assets/QtAssets.qrc 
