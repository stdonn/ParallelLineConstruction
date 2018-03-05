# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor

class HorizonConstructData():
    def __init__(self, construct_horizon=True, base_horizon=False, name="unknown", thickness=1,
                 color=QColor(255, 255, 255, 0)):
        self.construct_horizon = construct_horizon
        self.base_horizon = base_horizon
        self.name = name
        self.thickness = thickness
        self.color = color

    def __repr__(self):
        return "HorizonConstructData <{}, {}, {}, {}, {}>".format(self.name, self.construct_horizon, self.base_horizon,
                                                                  self.thickness, self.color.name())

    def __str__(self):
        return "{}\n\tconstruct: {}\n\tbase: {}\n\tthickness: {}\n\tcolor: {}".format(self.name, self.construct_horizon,
                                                                                      self.base_horizon,
                                                                                      self.thickness, self.color.name())