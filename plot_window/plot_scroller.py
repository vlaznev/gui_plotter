from collections import namedtuple
import plotter
from PyQt4 import Qt, QtCore, QtGui


def limit(value, min, max):
    if value < min:
        return min
    if value > max:
        return max
    return value

def iterableSubtract(iterable, value):
    result = []
    for itm in iterable:
        result.append(itm - value)
    return tuple(result)


class Anchor:
    Left = 0
    Right = 1

class MouseMode:
    Select = 1
    Resize = 2

NearestItem = namedtuple("NearestItem", ['value', 'index', 'distance'], verbose=False)
def getNearestItem(array, value):
    """ returns NearestItem """
    result = None
    for i in xrange(len(array)):
        distance = abs(array[i] - value)
        if result is None or distance < result[2]:
            result = NearestItem(value=array[i], index=i, distance=distance)
    return result

class Selection:
    def __init__(self):
        self._edges = [0,0]

    def min(self):
        return min(self._edges)

    def max(self):
        return max(self._edges)

    def first(self):
        return self._edges[0]

    def last(self):
        return self._edges[1]

    def center(self):
        return sum(self._edges) / 2

    def width(self):
        return abs(self._edges[1] - self._edges[0])

    def edges(self):
        return tuple(self._edges)

    def setEdges(self, first, last):
        self._edges = [first, last]
        return self


    def setFirst(self, value):
        self._edges[0] = value
        return self

    def setLast(self, value):
        self._edges[1] = value
        return self

    def setCenterAndWidth(self, center, width):
        self.setFirst(center - width / 2)
        self.setLast( self._edges[0] + width)
        return self

    def moveCenterTo(self, center):
        self.moveBy(center - self.center())
        return self

    def moveBy(self, distance):
        self._edges[0] += distance
        self._edges[1] += distance
        return self

    def moveEdgeTo(self, edgeIndex, value):
        self._edges[edgeIndex] = value
        return self

    def limit(self, minLimit, maxLimit):
        if maxLimit < minLimit:
            minLimit, maxLimit = maxLimit, minLimit

        w = min(self.width(), maxLimit - minLimit)

        center = limit(self.center(), minLimit + (w/2), maxLimit - (w/2))
        self.setCenterAndWidth(center, w)
        return self



class PlotScroller(plotter.Plotter):
    def __init__(self, parent=None, background=Qt.Qt.black):
        super(PlotScroller, self).__init__(parent=parent, background=background)
        self.maxValue = 0
        self.selection = Selection()
        self.selectionAnchor = Anchor.Left

        self.selectRectColor = QtGui.QColor(Qt.Qt.green)
        self.selectRectColor.setAlpha(100)

        self._mouseMode = None # mode of mouse operation. Can be None, MouseMode.Select, MouseMode.Resize
        self.lastMouseX = 0
        self._resizingEdgeIndex = None #index of edge to move

        self.setMouseTracking(True)
        self.cursorChanged = False

    def getScale(self):
        if self.maxValue > 0:
            return float(self.width()) / self.maxValue
        else:
            return 1

    def posToScreen(self, pos):
        return pos * self.getScale()

    def screenToPos(self, screenCoords):
        return screenCoords / self.getScale()

    def _updateAnchor(self):
        if self.selection.max() == self.maxValue:
            self.selectionAnchor = Anchor.Right
        else:
            self.selectionAnchor = Anchor.Left

    def _updateSelectionWithMouse(self, coords):
        first, last = map(self.screenToPos, coords)
        self.selection.setEdges(first, last)
        self.selection.limit(0, self.maxValue)
        self._updateAnchor()

    def _moveSelectionWithMouse(self, mouseX):
        self.selection.moveCenterTo( self.screenToPos(mouseX) )
        self.selection.limit(0, self.maxValue)
        self._updateAnchor()

    def mousePressEvent(self, event):
        self.lastMouseX = event.x()
        if event.button() == Qt.Qt.RightButton:
            self._moveSelectionWithMouse(self.lastMouseX)
            self.repaint()
            self.emitSelectionChanged()
        else:
            edgeIndex = self.snapToSelectionEdge(self.lastMouseX)
            if edgeIndex is not None:
                self._mouseMode = MouseMode.Resize
                self._resizingEdgeIndex = edgeIndex
            else:
                self._mouseMode = MouseMode.Select
                self.selectionAnchor = Anchor.Left
                pos = limit(self.screenToPos(self.lastMouseX), 0, self.maxValue)
                self.selection.setEdges(pos, pos)
                self.repaint()
                self.emitSelectionChanged()


    def mouseMoveEvent(self, event):
        self.lastMouseX = event.x()

        if event.buttons() & Qt.Qt.RightButton:
            self._moveSelectionWithMouse(self.lastMouseX)
            self.repaint()
            self.emitSelectionChanged()

        elif self._mouseMode == MouseMode.Select:
            self.selection.setLast( self.screenToPos(limit(event.x(), 0, self.width()) ) )
            self._updateAnchor()
            self.repaint()
            self.emitSelectionChanged()

        elif self._mouseMode == MouseMode.Resize:
            pos = self.screenToPos(limit(self.lastMouseX, 0, self.width()))
            self.selection.moveEdgeTo(self._resizingEdgeIndex,  pos)
            self._updateAnchor()
            self.repaint()
            self.emitSelectionChanged()

        elif self.snapToSelectionEdge(event.x()) is not None:
            self.setCursor(QtGui.QCursor(Qt.Qt.SizeHorCursor))
            self.cursorChanged = True

        elif self.cursorChanged:
            self.unsetCursor()
            self.cursorChanged = False

    def getSelectionCoords(self):
        return self.posToScreen(self.selection.min()), self.posToScreen(self.selection.max())

    def snapToSelectionEdge(self, mouseX):
        item = getNearestItem(self.getSelectionCoords(), mouseX)
        if item.distance < 2:
            return item.index
        else:
            return None

    def mouseReleaseEvent(self, event):
        self._mouseMode = None
        self._resizingEdgeIndex = None

    def wheelEvent(self, event):
        orient = event.orientation()
        if orient == Qt.Qt.Vertical:
            delta = float(event.delta()) / 120
            self.setSelectionWidth(self.selection.width() * (1 +  delta/10))
            if self.selectionAnchor == Anchor.Right:
                self.selection.moveBy(self.maxValue - self.selection.max())
            self.emitSelectionChanged()

    def paintEvent(self, event):
        selectRect = self.getSelectionQRect()
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
        if self._mouseMode is not None:
            pos = self.screenToPos(limit(self.lastMouseX, 0, self.width()) )
            if self._mouseMode == MouseMode.Select:
                self.selection.setLast( pos )
            else:
                self.selection.moveEdgeTo(self._resizingEdgeIndex, pos)
            self.repaint()
            self.emitSelectionChanged()
        elif self.selectionAnchor == Anchor.Right:
            self.selection.moveBy(value - oldValue)
            self.selection.limit(0, self.maxValue)
            self.emitSelectionChanged()

    def moveSelectionBy(self, delta):
        self.selection.moveBy(delta)
        self.selection.limit(0, self.maxValue)

    def setSelectionWidth(self, value):
        self.selection.setCenterAndWidth(self.selection.center(), value)
        self.selection.limit(0, self.maxValue)

    def getSelectionQRect(self):
        scale = float(self.width()) / self.maxValue if self.maxValue else self.width()
        left = self.posToScreen(self.selection.min())
        width = self.posToScreen(self.selection.width())

        return QtCore.QRectF(left, 0, width, self.height())

    def emitSelectionChanged(self):
        self.selectionChanged.emit()


    selectionChanged = QtCore.pyqtSignal()


