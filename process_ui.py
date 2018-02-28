# -*- coding: utf-8 -*-
"""
remove process ui conversion and remove errors
"""

import PyQt5.pyrcc_main

without_resources = True

if __name__ == '__main__':
    files = ["C:\\Programmieren\\QGIS-Plugins\\ParallelLineConstruction\\resources.qrc"]
    outFileName = "C:\\Programmieren\\QGIS-Plugins\\ParallelLineConstruction\\resources.py"
    PyQt5.pyrcc_main.processResourceFile(files, outFileName, False)
