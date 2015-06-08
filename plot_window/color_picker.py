__author__ = 'user'

from PyQt4 import Qt, QtGui

class QColorComboBox(QtGui.QComboBox):
    ColorNames = ["darkGreen", "green", "gray", "red", "white", "blue", "cyan", "darkMagenta", "yellow",
                  "darkRed", "black", "magenta"]

    ColorRole = Qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(QColorComboBox, self).__init__(parent)
        self.fillColors()


    def fillColors(self):
        size = self.style().pixelMetric(QtGui.QStyle.PM_SmallIconSize)
        pixmap = QtGui.QPixmap(size, size)

        idx = 0
        for colorName in self.ColorNames:
            color = QtGui.QColor(colorName)
            self.addItem(colorName, QtGui.QColor(idx))
            pixmap.fill(color)
            self.setItemData(idx, pixmap, Qt.Qt.DecorationRole)
            self.setItemData(idx, color, self.ColorRole)
            idx += 1

    def currentColor(self):
        idx = self.currentIndex()
        if idx >= 0:
            return self.itemData(idx, self.ColorRole)
        else:
            return None

    def color(self, index):
        return self.itemData(index, self.ColorRole)

    def setCurrentColor(self, color):
        colorObject = QtGui.QColor(color)
        for idx in xrange(self.count()):
            if colorObject == self.color(idx):
                self.setCurrentIndex(idx)
                return
        raise ValueError("Color not found: " + str(color))
