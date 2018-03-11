# -*- coding: utf-8 -*-


from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsGeometry, QgsPoint
from qgis.gui import QgisInterface

import numpy as np
from typing import List, Tuple

from .HorizonConstruct import HorizonConstructData, HorizonConstructModel


class LineConstruction(QObject):
    """
    helper class for storing necessary data and the construction of lines
    """

    def __init__(self, iface: QgisInterface) -> None:
        """
        Initialization of the class
        """
        super().__init__()
        self.__iface = iface
        self.__active_geometry = None
        self.__active_line = None
        self.__line_normal = None
        self.__model = None
        self.__side = 1

        self.side_changed.connect(self.__construct_frame_lines)

    # signals
    side_changed = pyqtSignal(name='side_changed')

    # setter and getter
    @property
    def active_geometry(self) -> QgsGeometry:
        """
        returns self.__active_geometry
        :return: the currently active geometry
        """
        return self.__active_geometry

    @active_geometry.setter
    def active_geometry(self, geom: QgsGeometry or None):
        """
        Sets self.__active_geometry
        :raises TypeError: if geom is not of type QgsGeometry
        """
        if geom is None:
            self.__active_geometry = None
        if not isinstance(geom, QgsGeometry):
            raise TypeError("Parameter is not of type QgsGeometry")

        self.__active_geometry = geom

    @property
    def active_line(self) -> List[Tuple]:
        """
        Returns a list of Tuples with x, y coordinates of the current active geometry
        :return: Returns a list of Tuples with x, y coordinates of the current active geometry
        """
        return self.__active_line

    @active_line.setter
    def active_line(self, line: List[Tuple] or None) -> None:
        """
        Sets the currently active line as a list of Tuples with x, y coordinates
        :param line: current active line
        :return: Nothing
        :raises TypeError: if parameter is not a list or parameter items not tuples
        :raises ValueError: if len(tuple) is not equal to 2, or tuple coordinates are not convertable to type float
        """
        if line is None:
            self.__active_line = None
        if not isinstance(line, list):
            raise TypeError("Parameter is not a list")
        for elem in line:
            if not isinstance(elem, tuple):
                raise TypeError("List item is not a tuple")
            if len(elem) != 2:
                raise ValueError("Wrong number of items in tuple")
            if not (isinstance(elem[0], float) and isinstance(elem[1], float)):
                raise ValueError("Tuple items not compatible to float")

        self.__active_line = line

    @property
    def model(self) -> HorizonConstructModel:
        return self.__model

    @model.setter
    def model(self, mod: HorizonConstructModel or None) -> None:
        if mod is None:
            self.__model = None
        if not isinstance(mod, HorizonConstructModel):
            raise TypeError("Parameter is not of type HorizonConstructionModel")
        self.__model = mod

    @property
    def side(self) -> int:
        """
        Returns the current line side index
        -  0: on the line
        -  1: in line direction left
        - -1: in line direction right
        :return: Returns the current line side index
        """
        return self.__side

    def calc_side(self, pos: QgsPoint) -> None:
        """
        Calculates the direction of the line
        :return: Nothing
        """
        vertex = np.array(self.__active_line[0])
        vect = np.array(self.__active_line[-1]) - vertex
        self.__line_normal = np.array(-vect[1], vect[0])
        self.__line_normal = self.__line_normal / np.abs(self.__line_normal)

        p = np.array((pos.x(), pos.y()))
        d1 = np.dot(p, self.active_line[1])
        d2 = np.dot(self.active_line[0], self.active_line[1])

        side = np.sign(d1 - d2)
        side = side if side != 0 else 1
        if side != self.__side:
            self.__side = side
            self.side_changed.emit()

    # private functions
    def __construct_frame_lines(self) -> None:
        """
        Constructs the frame lines, based on the given HorizonConstructModel/-Data for further unit construction
        :return: Nothing
        """
        pass

    # public functions
    def reset(self) -> None:
        """
        Resets the object to the initialization stage
        :return: Nothing
        """
        self.__active_geometry = None
        self.__active_line = None
        self.__line_normal = None
        self.__model = None
        self.__side = 1

