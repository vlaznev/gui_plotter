import plotter
from PyQt4 import Qt, QtCore, QtGui


def limit(value, min, max):
    if value < min:
        return min
    if value > max:
        return max
    return value


class Anchor:
    Left = 0
    Right = 1

class PlotScroller(plotter.Plotter):
    def __init__(self, parent=None, background=Qt.Qt.black):
        super(PlotScroller, self).__init__(parent=parent, background=background)
        self.mouseStartPos = None
        self.mousePos = None
        self.selectionWidth = 0
        self.selectionPos = 0
        self.selectionAnchor = Anchor.Right

        self.selectRectColor = QtGui.QColor(Qt.Qt.green)
        self.selectRectColor.setAlpha(100)
        self.maxValue = 0
        self.mouseSelect = None

    def scale(self):
        if self.maxValue > 0:
            return float(self.width()) / self.maxValue
        else:
            return 1

    def _updateSelectionWithMouse(self):
        if self.mouseSelect is None:
            return False

        scale = self.scale()
        left, right = self.mouseSelect
        if right < left:
            left, right = (right, left)

        self.selectionPos = left / scale
        self.selectionWidth = (right - left) / scale
        return True

    def _moveSelectionWithMouse(self, mouseX):
        scale = float(self.width()) / self.maxValue
        pos = mouseX / scale
        self.setSelectionPos(pos - self.selectionWidth / 2)
        if self.selectionPos == self.maxValue - self.selectionWidth:
            self.selectionAnchor = Anchor.Right
        else:
            self.selectionAnchor = Anchor.Left

    def mousePressEvent(self, event):
        if event.button() == Qt.Qt.LeftButton:
            self._moveSelectionWithMouse(event.x())
        else:
            self.mouseSelect = [event.x(), event.x()]
            self.selectionAnchor = Anchor.Left
            self.setSelectionPos(event.x() * self.scale())
            self.selectionWidth = 0
        self.repaint()
        self.emitSelectionChanged()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.Qt.LeftButton:
            self._moveSelectionWithMouse(event.x())
        else:
            self.mouseSelect[1] = limit(event.x(), 0, self.width())
            self._updateSelectionWithMouse()
        self.repaint()
        self.emitSelectionChanged()

    def mouseReleaseEvent(self, event):
        self.mouseSelect = None

    def wheelEvent(self, event):
        orient = event.orientation()
        if orient == Qt.Qt.Vertical:
            delta = float(event.delta()) / 120
            self.setSelectionWidth(self.selectionWidth * (1 +  delta/10))
            self.emitSelectionChanged()

    def paintEvent(self, event):
        selectRect = self.getSelectionRect()
        bitmap = QtGui.QPixmap(self.size())
        self.plot(bitmap)
        p = QtGui.QPainter()
        p.begin(bitmap)
        p.fillRect(selectRect, self.selectRectColor)
        p.end()

        p.begin(self)
        p.drawPixmap(0, 0, bitmap)
        p.end()

    def setMaxValue(self, value):
        oldValue = self.maxValue
        self.maxValue = value
        if self.mouseSelect is not None:
            if self._updateSelectionWithMouse():
                self.emitSelectionChanged()
        elif self.selectionAnchor == Anchor.Right:
            self.selectionPos += value - oldValue
            self.emitSelectionChanged()

    def setSelectionPos(self, pos):
        self.selectionPos = limit(pos, 0, self.maxValue - self.selectionWidth)
        self.emitSelectionChanged()

    def setSelectionWidth(self, value):
        oldWidth = self.selectionWidth
        if self.selectionAnchor == Anchor.Left:
            newPos = self.selectionPos - (value - oldWidth) / 2
            self.selectionPos = limit(newPos, 0, self.maxValue - self.selectionWidth)
            self.selectionWidth = limit(value, 0, self.maxValue - self.selectionPos)
        else:
            self.selectionPos = self.selectionPos - (value - self.selectionWidth)
            self.selectionWidth = value
        self.emitSelectionChanged()

    def getSelectionRect(self):
        scale = float(self.width()) / self.maxValue if self.maxValue else self.width()
        left = scale * self.selectionPos

        return QtCore.QRectF(left, 0, scale * self.selectionWidth, self.height())

    def emitSelectionChanged(self):
        self.selectionChanged.emit()


    selectionChanged = QtCore.pyqtSignal()
