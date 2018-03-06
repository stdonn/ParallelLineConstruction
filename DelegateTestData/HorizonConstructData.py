# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor

from typing import List

class HorizonConstructData():
    def __init__(self, construct_horizon=True, base_horizon=False, name="unknown", thickness=1,
                 color=QColor(255, 255, 255)):
        self.__data = [None, None, None, None, None]
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
                                                                                      self.base_horizon, self.thickness,
                                                                                      self.color.name())

    def __getitem__(self, item: int or List[int]) -> object or List:
        return self.__data[item]

    @property
    def base_horizon(self) -> bool:
        return self.__data[1]

    @base_horizon.setter
    def base_horizon(self, value: bool) -> None:
        self.__data[1] = bool(value)

    @property
    def color(self) -> QColor:
        return self.__data[4]

    @color.setter
    def color(self, value: QColor) -> None:
        self.__data[4] = QColor(value)

    @property
    def construct_horizon(self) -> bool:
        return self.__data[0]

    @construct_horizon.setter
    def construct_horizon(self, value: bool) -> None:
        self.__data[0] = bool(value)

    @property
    def name(self) -> str:
        return self.__data[2]

    @name.setter
    def name(self, value: str) -> None:
        self.__data[2] = str(value)

    @property
    def thickness(self) -> int:
        return self.__data[3]

    @thickness.setter
    def thickness(self, value: int) -> None:
        self.__data[3] = int(value)
