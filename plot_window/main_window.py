#!/usr/bin/python

import sys
import input_parsers_gui
from PyQt4 import Qt, QtGui
from plotter import Plotter
from plot_scroller import PlotScroller, Anchor
import math
import itertools
import collections
from log_viewer import LogViewer



def emptyGenerator():
    """ Generator that returns nothing """
    return
    yield


def floatRange(begin, end, step):
    value = float(begin)
    limit = float(end)
    increment = float(step)
    if value + increment <= value:
        raise ValueError('Invalid step: possible infinite loop (begin=%f, end=%f, step=%f)' % (begin, end, step))

    while value < limit:
        yield value
        value += increment


class CurveData(object):
    def __init__(self, info, offset):
        self.info = info
        self.data = []
        self.offset = offset


class MainWindow(QtGui.QDialog):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.MAX_LINES = 1000
        self.dataSource = emptyGenerator()

        self.input = []
        self.totalLines = 0
        self.curve = collections.defaultdict(self.createCurveData)
        self.nextCurveId = 0
        self.maxValue = 1

        self.plot = Plotter()
        self.plot.setDataGetter(self.mainPlotGetter)
        self.plot.setCurveGetter(self.curveGetter)
        self.plot.setMouseTracking(True)

        self.plotScroller = PlotScroller()
        self.plotScroller.setDataGetter(self.plotScrollerGetter)
        self.plotScroller.setCurveGetter(self.curveGetter)
        self.plotScroller.selectionChanged.connect(self.onScrollerChanged)

        self.inputView = LogViewer()
        self.inputView.setMaxLineCount(500)
        self.parsersPanel = input_parsers_gui.ParserListPanel()
        self.parsersPanel.itemsChanged.connect(self.onParsersChanged)

        self.rightPanel = QtGui.QVBoxLayout()
        self.rightPanel.addWidget(self.parsersPanel)
        self.rightPanel.setStretch(1, 1)

        self.leftPanel = QtGui.QVBoxLayout()
        self.leftPanel.addWidget(QtGui.QLabel("Details graph"))
        self.leftPanel.setStretch(0, 0)
        self.leftPanel.addWidget(self.plot)
        self.leftPanel.setStretch(1, 1)
        self.leftPanel.addWidget(QtGui.QLabel("Input graph (select range to detail with right-click):"))
        self.leftPanel.setStretch(2, 0)
        self.leftPanel.addWidget(self.plotScroller)
        self.leftPanel.setStretch(3, 1)
        self.leftPanel.addWidget(QtGui.QLabel("Input lines:"))
        self.leftPanel.setStretch(4, 0)
        self.leftPanel.addWidget(self.inputView)
        self.leftPanel.setStretch(5, 1)

        self.layout = QtGui.QGridLayout(self)
        self.layout.addLayout(self.leftPanel, 0, 0)
        self.layout.addLayout(self.rightPanel, 0, 1)
        self.layout.setColumnStretch(0, 1)

        self.resize(600, 500)
        self.startTimer(50)

        self.oldSelection = None

    def addCurves(self, curves):
        for c in curves:
            pattern = c['pattern']
            color = c['color']
            group = c.get('group', 1)
            curve = input_parsers_gui.DataCurve(self.nextCurveId, pattern, [ group ], color )
            self.parsersPanel.addDataCurve(curve)
            self.nextCurveId += 1

    def createCurveData(self):
        return CurveData(None, self.totalLines)

    def curveGetter(self):
        return ((c.info.id(), c.info.qtColor()) for c in self.curve.values())

    def buildTuple(self, x, y, step, scale, height):
        screenX = step * x
        if y is  None:
            screenY = None
        else:
            screenY = height - (scale * y + height/2)
        return (screenX, screenY, x, y)

    def mainPlotGetter(self, curveId, width, height):
        if curveId not in self.curve or self.plotScroller.selectionWidth == 0:
            return emptyGenerator()
        curve = self.curve[curveId]
        data = curve.data
        offset = curve.offset
        minIndex = self.plotScroller.selectionPos
        maxIndex = self.plotScroller.selectionPos + self.plotScroller.selectionWidth

        if maxIndex < offset:
            return emptyGenerator()

        if minIndex > offset:
            minIndex -= offset
            maxIndex -= offset
            start = 0
        else:
            start = offset - minIndex
            minIndex = 0
            maxIndex -= offset

        step = float(width) / (maxIndex - minIndex + start)
        scale = 0.9 * (height / 2) / self.maxValue
        coords = itertools.izip(itertools.count(start), itertools.islice(data, minIndex, maxIndex))
        return itertools.imap(lambda xy: self.buildTuple(xy[0], xy[1], step, scale, height), coords)

    def plotScrollerGetter(self, curveId, width, height):
        if curveId not in self.curve:
            return emptyGenerator()

        data = self.curve[curveId].data
        offset = self.curve[curveId].offset
        if not data:
            return emptyGenerator()

        scale = 0.9 * (height / 2) / self.maxValue
        step = float(width) / self.totalLines
        coords = itertools.izip(itertools.count(offset), data)
        return itertools.imap(lambda xy: self.buildTuple(xy[0], xy[1], step, scale, height), coords)

    def onScrollerChanged(self):
        minIndex = self.plotScroller.selectionPos
        maxIndex = self.plotScroller.selectionPos + self.plotScroller.selectionWidth
        self.oldSelection = (minIndex, maxIndex)
        self.plot.replot()

    def onParsersChanged(self, index):
        newCurves = dict((x.id(), x) for x in self.parsersPanel.dataCurves())
        toDelete = [key for key in self.curve if key not in newCurves]

        for key in toDelete:
            del self.curve[key]

        for key in newCurves:
            self.curve[key].info = newCurves[key]

        self.plot.replot()
        self.plotScroller.replot()

    def timerEvent(self, QTimerEvent):
        if self.dataSource is None:
            return

        try:
            newLine = self.dataSource.next()
        except StopIteration:
            return

        if newLine:
            newLine = newLine.strip()

        if not newLine:
            return

        if self.curve:
            for curve in self.curve.values():
                parser = curve.info.parser()
                data = curve.data
                res = parser.parse(newLine)
                if res:
                    value = float(res[0])
                    if self.maxValue < abs(value):
                        self.maxValue = abs(value)
                    data.append(value)
                else:
                    data.append(None)

        self.inputView.addLine(newLine)
        self.totalLines += 1
        updatesEnabled = self.plot.updatesEnabled()
        self.plot.setUpdatesEnabled(False)
        if self.MAX_LINES is not None and self.totalLines > self.MAX_LINES:
            delta = self.totalLines - self.MAX_LINES
            self.totalLines -= delta
            for curve in self.curve.values():
                if curve.offset >= delta:
                    curve.offset -= delta
                else:
                    toCut = delta - curve.offset
                    curve.offset = 0
                    del curve.data[0:toCut]
            if self.plotScroller.selectionAnchor != Anchor.Right:
                self.plotScroller.setSelectionPos(self.plotScroller.selectionPos - delta)
            self.plot.replot()
        self.plotScroller.setMaxValue(self.totalLines)
        self.plot.setUpdatesEnabled(updatesEnabled)
        self.plotScroller.replot()
