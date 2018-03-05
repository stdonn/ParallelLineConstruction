# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor


class HorizonConstructData():
    def __init__(self, construct_horizon=True, base_horizon=False, name="unknown", thickness=1,
                 color=QColor(255, 255, 255, 0)):
        self.data = [
            construct_horizon,
            base_horizon,
            name,
            thickness,
            color
        ]

    def __repr__(self):
        return "HorizonConstructData <{}, {}, {}, {}, {}>".format(self.data[2], self.data[0], self.data[1],
                                                                  self.data[3], self.data[4].name())

    def __str__(self):
        return "{}\n\tconstruct: {}\n\tbase: {}\n\tthickness: {}\n\tcolor: {}".format(self.data[2], self.data[0],
                                                                                      self.data[1], self.data[3],
                                                                                      self.data[4].name())
