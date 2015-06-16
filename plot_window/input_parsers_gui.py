from PyQt4 import Qt, QtGui, QtCore
from input_parsers import DataCurve, InputParser
import re
import itertools
import color_picker
import time


class InputParserEditDialog(QtGui.QDialog):
    ColorRole = Qt.Qt.UserRole + 1

    def __init__(self, parent=None):
        super(InputParserEditDialog, self).__init__(parent)
        self.setWindowTitle("Parser editor")

        self.colorPicker = color_picker.QColorComboBox()

        self.filterEdit = QtGui.QLineEdit()
        self.filterEdit.textChanged.connect(self.updateTestResult)

        self.groupsEdit = QtGui.QLineEdit()
        self.groupsEdit.textChanged.connect(self.updateTestResult)

        self.testEdit = QtGui.QLineEdit()
        self.testEdit.textChanged.connect(self.updateTestResult)

        self.testResult = QtGui.QLabel()

        self.okButton = QtGui.QPushButton("OK")
        self.okButton.clicked.connect(self.accept)
        self.okButton.setEnabled(False)

        self.cancelButton = QtGui.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)

        self.buttonsLayout = QtGui.QHBoxLayout()
        self.buttonsLayout.addWidget(self.okButton)
        self.buttonsLayout.addWidget(self.cancelButton)

        self.layout = QtGui.QFormLayout(self)
        self.layout.addRow("Curve color:", self.colorPicker)
        self.layout.addRow("Filter regexp:", self.filterEdit)
        self.layout.addRow("Groups to extract:", self.groupsEdit)
        self.layout.addRow("Test input:", self.testEdit)
        self.layout.addRow("Extraction result:", self.testResult)
        self.layout.addRow(self.buttonsLayout)
        self.setMinimumWidth(400)
        


    def execute(self):
        return self.exec_() == QtGui.QDialog.Accepted

    def setData(self, pattern, groups, color):
        self.filterEdit.setText(pattern)
        self.groupsEdit.setText(', '.join(map(str, groups)))
        self.colorPicker.setCurrentColor(color)

    def pattern(self):
        return str(self.filterEdit.text())

    def groups(self):
        text = self.groupsEdit.text()
        if text:
            return map(int, self.groupsEdit.text().split(','))
        else:
            return []

    def color(self):
        return self.colorPicker.currentColor()


    def enterNewDataCurve(self):
        self.setData('', [], Qt.Qt.yellow)
        curveId = time.time()
        if self.execute():
            return DataCurve(curveId, InputParser(self.pattern(), self.groups()), self.color())
        else:
            return None

    def editDataCurve(self, curve):
        self.setData(curve.parser().pattern, curve.parser().groups, curve.color())
        if self.execute():
            return DataCurve(curve.id(), InputParser(self.pattern(), self.groups()), self.color())
        else:
            return None

    def updateTestResult(self, event):
        try:
            pattern = self.pattern()
            groups = self.groups()
            test = str(self.testEdit.text())
            if not pattern or not groups:
                self.testResult.setText('')
                self.okButton.setEnabled(False)
                return

            if not test:
                self.testResult.setText('')
                self.okButton.setEnabled(True)
                return
            self.okButton.setEnabled(False)

            regex = re.compile(pattern)
            m = regex.search(test)
            if m:
                res = map(str, map(m.group, groups))
                self.testResult.setText("Match: %s\nExtracted data: [%s]" % (str(m.group(0)), ','.join(res)))
            else:
                self.testResult.setText("No match")

            self.okButton.setEnabled(True)
        except Exception as ex:
            self.testResult.setText('Error: ' + ex.message)


class ParserListItem(QtGui.QListWidgetItem):
    def __init__(self, curve):
        super(ParserListItem, self).__init__()
        self._curve = None
        self.setDataCurve(curve)

    def dataCurve(self):
        return self._curve

    def setDataCurve(self, curve):
        self._curve = curve
        self.setText(str(curve))
        self.setData(Qt.Qt.DecorationRole, curve.qtColor())

class ParserListItemPainter(QtGui.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ParserListItemPainter, self).__init__(parent)

    def paint(self, painter, option, item):
        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.color(QtGui.QPalette.Highlight))

        text = str(item)
        color = item.color
        r = option.rect.adjusted(5,0,0,-5)
        if not isinstance(color, QtGui.QColor):
            color = QtGui.QColor(color)
        painter.fillRect(r, color)

    def sizeHint(self, option, index):
        return QtCore.QSize(100, 25)

class ParserListPanel(QtGui.QWidget):

    itemsChanged = Qt.pyqtSignal(int)

    def __init__(self, parent=None):
        super(ParserListPanel, self).__init__(parent)
        self.label = QtGui.QLabel("Input parsers")

        self.addButton = QtGui.QPushButton("Add")
        self.addButton.clicked.connect(self.addParserClicked)

        self.editButton = QtGui.QPushButton("Edit")
        self.editButton.clicked.connect(self.editParserClicked)

        self.deleteButton = QtGui.QPushButton("Delete")
        self.deleteButton.clicked.connect(self.deleteParserClicked)

        self.list = QtGui.QListWidget()
        self.list.itemDoubleClicked.connect(self.editParserClicked)

        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.label, 0, 0, 1, 3)
        self.layout.addWidget(self.list, 1, 0, 1, 3)
        self.layout.addWidget(self.addButton, 2, 0)
        self.layout.addWidget(self.editButton, 2, 1)
        self.layout.addWidget(self.deleteButton, 2, 2)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def addDataCurve(self, curve):
        item = ParserListItem(curve)
        index = self.list.count()
        self.list.addItem(item)
        self.itemsChanged.emit(index)


    def addParserClicked(self, event):
        editor = InputParserEditDialog(self)
        curve = editor.enterNewDataCurve()
        if curve:
            self.addDataCurve(curve)

    def editParserClicked(self, event):
        editor = InputParserEditDialog(self)
        oldCurve = self.current()
        curve = editor.editDataCurve(oldCurve)
        if curve:
            self.replaceCurrent(curve)

    def deleteParserClicked(self, event):
        self.list.takeItem(self.list.currentRow())
        self.itemsChanged.emit(-1)

    def current(self):
        return self.list.currentItem().dataCurve()

    def replaceCurrent(self, curve):
        index = self.list.currentRow()
        item = self.list.currentItem()
        item.setDataCurve(curve)
        self.itemsChanged.emit(index)

    def dataCurve(self, index):
        return self.list.item(index).dataCurve()

    def dataCurves(self):
        items = itertools.imap(self.list.item, xrange(self.list.count()))
        return itertools.imap(ParserListItem.dataCurve, items)