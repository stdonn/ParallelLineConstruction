# -*- coding: utf-8 -*-

from qgis.core import QgsGeometry
from qgis.gui import QgisInterface

from typing import List, Tuple

class LineConstruction:
    """
    helper class for storing necessary data and the construction of lines
    """

    def __init__(self, iface: QgisInterface) -> None:
        """
        Initialization of the class
        """
        self.__iface = iface
        self.__active_geometry = None
        self.__active_line = None

    @property
    def active_geometry(self) -> QgsGeometry:
        """
        returns self.__active_geometry
        :return: the currently active geometry
        """
        return self.__active_geometry

    @active_geometry.setter
    def active_geometry(self, geom:QgsGeometry):
        """
        Sets self.__active_geometry
        :raises TypeError: if geom is not of type QgsGeometry
        """
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
    def active_line(self, line: List[Tuple]) -> None:
        """
        Sets the currently active line as a list of Tuples with x, y coordinates
        :param line: current active line
        :return: Nothing
        :raises TypeError: if parameter is not a list or parameter items not tuples
        :raises ValueError: if len(tuple) is not equal to 2, or tuple coordinates are not convertable to type float
        """
        if not isinstance(line, list):
            raise TypeError("Parameter is not a list")
        for elem in list:
            if not isinstance(elem, tuple):
                raise TypeError("List item is not a tuple")
            if len(elem) != 2:
                raise ValueError("Wrong number of items in tuple")
            try:
                elem[0] = float(elem[0])
                elem[1] = float(elem[1])
            except ValueError:
                raise ValueError("Tuple items not compatible to float")

        self.__active_line = line

