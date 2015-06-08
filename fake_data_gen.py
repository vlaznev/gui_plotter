#!/usr/bin/python

import itertools
import math


def sin_gen(scale, phase, step):
    """ sine generator """
    while 1:
        yield math.sin(phase) * scale
        phase += step


def square_gen(height, width, step=1):
    value = 0
    while 1:
        yield ((value / width) % 2) * height
        value += step


sine = sin_gen(0.5, 0, math.pi / 90)
square = square_gen(1, 90)

FakeDataGenerator = ("angle %f distance %f" % (sine.next(), square.next()) for i in itertools.count())

