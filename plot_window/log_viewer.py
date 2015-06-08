from PyQt4 import QtGui

class LogViewer(QtGui.QPlainTextEdit):
    def __init__(self, parent = None):
        super(LogViewer, self).__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
#        self.setHorizontalScrollBarPolicy(Qt.Qt.ScrollBarAlwaysOn)
#        self.setVerticalScrollBarPolicy(Qt.Qt.ScrollBarAsNeeded)

    def addLine(self, line):
        self.appendPlainText(line)

    def addLines(self, lines):
        for line in lines:
            self.appendPlainText(line)

    def setLines(self, lines):
        self.setPlainText("\n".join(lines))
    
    def setMaxLineCount(self, value):
        self.setMaximumBlockCount(value)