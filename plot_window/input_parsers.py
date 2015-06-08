__author__ = 'user'

import itertools
import re
import PyQt4.QtGui as QtGui


class InputParser(object):
    def __init__(self, pattern, groups):
        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.groups = groups

    def parse(self, line):
        res = self.regex.search(line)
        if res:
            return list(x for x in itertools.imap(res.group, self.groups))
        else:
            return []

    def __str__(self):
        return "[%s] on /%s/" % (','.join(map(str, self.groups)), self.pattern)

class DataCurve(object):
    def __init__(self, id, *args):
        self._id = id
        if len(args) == 2:
            parser = args[0]
            color = args[1]
        elif len(args) == 3:
            parser = InputParser(args[0], args[1])
            color = args[2]
        self._parser = parser
        self._color = color
        self._qtColor = QtGui.QColor(color)

    def id(self):
        return self._id

    def parser(self):
        return self._parser

    def color(self):
        return self._color

    def qtColor(self):
        return self._qtColor;

    def __str__(self):
        return str(self._parser)