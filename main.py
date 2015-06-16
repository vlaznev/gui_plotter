#!/usr/bin/python

import sys
from plot_window import MainWindow
from PyQt4 import QtGui

import serial
from threaded_reader import ThreadedReader

from fake_data_gen import FakeDataGenerator

# to read data from serail port uncomment this:
"""
source = ThreadedReader(serial.Serial("/dev/ttyS0"))
curves = [ {'color':'yellow', 'pattern':'(\d+)' } ]
"""

# to see the example with generaed data uncomment this:

source = FakeDataGenerator
curves = [
              {
                  'color' : 'yellow',
                  'pattern' :  "angle (\S+) distance (\S+)",
                  'group' : 1
              },
              {
                  'color' : 'red',
                  'pattern' :  "angle (\S+) distance (\S+)",
                  'group' : 2
              },
         ]

# to read data from file, uncomment this:
"""
source = open('datafile.txt', 'r')
curves = [ ['pattern': '(\d+)', 'color':'yellow'} ]
"""

app = QtGui.QApplication(sys.argv)
window = MainWindow()

window.dataSource = source
window.addCurves(curves)
window.maxValue = 1     # default scale
window.MAX_LINES = 100 # maximum points to store, can be None if no limit
window.show()

app.exec_()
