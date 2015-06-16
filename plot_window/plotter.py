from PyQt4 import Qt, QtGui, QtCore
import collections


def toQPoint(pt):
    return QtCore.QPoint(float(pt[0]), float(pt[1]))


def toQPointF(pt):
    return QtCore.QPointF(float(pt[0]), float(pt[1]))


class Plotter(QtGui.QWidget):
    def __init__(self, parent=None, background=Qt.Qt.black):
        super(Plotter, self).__init__(parent)
        self._curves = collections.defaultdict(list)
        self._background = background
        self._dataGetter = None
        self._curveGetter = None

    def addCurve(self, id, color):
        self._curves[str(id)] = QtGui.QPen(color)

    def setDataGetter(self, getter):
        self._dataGetter = getter

    def setCurveGetter(self, getter):
        self._curveGetter = getter

    def setBackground(self, color):
        self._background = color
        self.repaint()

    def paintEvent(self, event):
        bitmap = QtGui.QPixmap(self.size())
        self.plot(bitmap)
        p = QtGui.QPainter()
        p.begin(self)
        p.drawPixmap(0, 0, bitmap)
        p.end()

    def distanceSqr(self, p1, p2):
        return (p1[0]-p2[0])**2 + (p1[1] - p2[1])**2

    def plot(self, paintDevice):
        painter = QtGui.QPainter()
        width = paintDevice.width()
        height = paintDevice.height()
        mousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        mouse = (mousePos.x(), mousePos.y())
        nearest = None
        distanceToNearest = None

        rect = QtCore.QRect(0, 0, width, height)
        painter.begin(paintDevice)
        painter.fillRect(rect, self._background)
        if self._curveGetter:
            for curveId, pen in self._curveGetter():
                painter.setPen(pen)
                prev = None
                for coords in self._dataGetter(curveId, width, height):
                    if prev is None:
                        prev = coords
                        continue
                    if coords and coords[0] is not None and coords[1] is not None:
                        distance =  self.distanceSqr(coords, mouse)
                        if not nearest or distanceToNearest > distance:
                            nearest = tuple(coords)
                            distanceToNearest = distance
                        if prev[0] is not None and prev[1] is not None:
                            painter.drawLine(prev[0], prev[1], coords[0], coords[1])
                    elif prev and prev[0] is not None and prev[1] is not None:
                            painter.drawPoint(prev[0], prev[1])
                    prev = coords

        if nearest and self.distanceSqr(nearest, mouse) < 9:
            painter.setPen(Qt.Qt.white)
            painter.drawEllipse(nearest[0]-1, nearest[1]-1, 3, 3)
            painter.drawText(mouse[0], mouse[1], str(nearest[-1]))

        painter.end()

    def replot(self):
        self.repaint()
