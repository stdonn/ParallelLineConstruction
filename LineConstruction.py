# -*- coding: utf-8 -*-


from PyQt5.QtCore import QObject, QVariant, pyqtSignal
from qgis.core import QgsGeometry, QgsFeature, QgsField, QgsMapLayer, QgsMessageLog, QgsPoint, QgsPointXY, QgsProject, \
    QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgisInterface, QgsRubberBand

import numpy as np
from typing import List, Tuple

import sys, traceback

from .HorizonConstruct import HorizonConstructModel
from .parallel_line_construction_dockwidget import ParallelLineConstructionDockWidget


class LineConstruction(QObject):
    """
    helper class for storing necessary data and the construction of lines
    """

    def __init__(self, iface: QgisInterface, dockwidget: ParallelLineConstructionDockWidget) -> None:
        """
        Initialization of the class
        """
        super().__init__()
        self.__iface = iface
        self.__active_geometry = None
        self.__active_line = None
        self.__dockwidget = dockwidget
        self.__line_normal = None
        self.__model = None
        self.__side = 0
        self.__tmp_units = list()

        self.side_changed.connect(self.__construct_frame_lines)
        self.__dockwidget.line_join_style.currentIndexChanged.connect(self.__construct_frame_lines)

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
    def active_line(self) -> List[QgsPointXY]:
        """
        Returns a list of Tuples with x, y coordinates of the current active geometry
        :return: Returns a list of Tuples with x, y coordinates of the current active geometry
        """
        return self.__active_line

    @active_line.setter
    def active_line(self, line: List[QgsPointXY] or None) -> None:
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
            if not isinstance(elem, QgsPointXY):
                raise TypeError("List item is not a QgsPointXY")

        self.__active_line = line

    @property
    def model(self) -> HorizonConstructModel:
        return self.__model

    @model.setter
    def model(self, mod: HorizonConstructModel or None) -> None:
        if self.__model is not None:
            self.__model.dataChanged.disconnect(self.__construct_frame_lines)
        if mod is None:
            self.__model = None
        if not isinstance(mod, HorizonConstructModel):
            raise TypeError("Parameter is not of type HorizonConstructionModel")
        self.__model = mod
        self.__model.dataChanged.connect(self.__construct_frame_lines)

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

    @side.setter
    def side(self, side: int) -> None:
        """
        Sets the current side
        :param side: current side. Parameter muss be -1 or 1
        :return: Nothing
        :raises ValueError: if value is not of type int
        """
        side = np.sign(int(side))
        if side != self.__side:
            self.__side = side
            self.side_changed.emit()

    def calc_side(self, pos: QgsPoint) -> None:
        """
        Calculates the direction of the line
        :return: Nothing
        """
        if self.__active_line is None:
            self.__side = 0
            return
        vertex = np.array(self.__active_line[0])
        vect = np.array(self.__active_line[-1])
        vect -= vertex
        self.__line_normal = np.array((-1 * vect[1], vect[0]))
        self.__line_normal = self.__line_normal / np.linalg.norm(self.__line_normal)

        p = np.array((pos.x(), pos.y()))
        d1 = np.dot(p, self.__line_normal)
        d2 = np.dot(self.active_line[0], self.__line_normal)

        side = np.sign(d1 - d2)
        side = side if side != 0 else 1
        if side != self.__side:
            self.__side = side
            self.side_changed.emit()

    def __reset_tmp_units(self) -> None:
        """
        Removes all constructed rubberbands from the curren QGIS canvas
        :return: Nothing
        """
        for band in self.__tmp_units:
            band[1].hide()
            del band[1]

        self.__tmp_units = list()
        self.__dockwidget.construct.setEnabled(False)
        try:
            self.__dockwidget.construct.clicked.disconnect(self.__build_lines)
        except TypeError:
            pass

    # private functions
    def __construct_frame_lines(self, _: object = None, _1: object = None, _2: object = None) -> None:
        """
        Constructs the frame lines, based on the given HorizonConstructModel/-Data for further unit construction

        It includes 3 temporary parameters for different signal connections
        :return: Nothing
        """

        # first: reset exisiting rubberband
        self.__reset_tmp_units()

        if self.__side == 0 or self.active_geometry is None:
            return

        sum_distances = 0
        join_style = self.__dockwidget.line_join_style.currentIndex() + 1
        text = "Join style: {}".format(join_style)
        self.__dockwidget.notifications.setText(text)
        # upwards
        base_item_index = self.__model.base_item_index
        for row_index in range(base_item_index, self.__model.rowCount()):
            row = self.__model.row(row_index)
            if row.construct_horizon:
                geometry = self.active_geometry.offsetCurve(sum_distances, 8, join_style,
                                                            10 * sum_distances * (-1 if sum_distances < 0 else 1))
                rubberband = QgsRubberBand(self.__iface.mapCanvas(), QgsWkbTypes.LineGeometry)
                color = row.color
                color.setAlpha(150)
                rubberband.setColor(color)
                rubberband.addGeometry(geometry)
                rubberband.show()
                self.__tmp_units.append([row.name, rubberband])
            sum_distances += row.distance * self.side * -1

        # downwards
        sum_distances = 0
        for row_index in range(base_item_index - 1, -1, -1):
            row = self.__model.row(row_index)
            sum_distances -= row.distance * self.side * -1
            if row.construct_horizon:
                geometry = self.active_geometry.offsetCurve(sum_distances, 8, join_style,
                                                            10 * sum_distances * (-1 if sum_distances < 0 else 1))
                rubberband = QgsRubberBand(self.__iface.mapCanvas(), QgsWkbTypes.LineGeometry)
                color = row.color
                color.setAlpha(150)
                rubberband.setColor(color)
                rubberband.addGeometry(geometry)
                rubberband.show()
                self.__tmp_units.append([row.name, rubberband])

        self.__dockwidget.construct.setEnabled(True)
        self.__dockwidget.construct.clicked.connect(self.__build_lines)

    def __build_lines(self) -> None:
        """
        Save the current self.__tmp_units in an in-memory layer called 'Parallel Unit Lines'
        Create a layer with the given name if it is not existing
        :return: Nothing
        """
        unit_list = list()
        for unit in self.__tmp_units:
            unit_list.append([unit[0], unit[1].asGeometry()])

        lyrs = [lyr for lyr in self.__iface.mapCanvas().layers() if lyr.name() == "Parallel Unit Lines"]
        if len(lyrs) == 0:
            current_layer = self.__iface.mapCanvas().currentLayer()
            crs = QgsProject.instance().crs().toWkt()
            uri = "linestring?crs=wkt:{}&field=name:string(255)".format(crs)
            vector_layer = QgsVectorLayer(uri, "Parallel Unit Lines", "memory")
            QgsProject.instance().addMapLayer(vector_layer)
            self.__iface.mapCanvas().setCurrentLayer(current_layer)
        else:
            vector_layer = lyrs[0]

        if (not vector_layer.isValid()) or (vector_layer.type() != QgsMapLayer.VectorLayer):
            self.__iface.messageBar().pushCritical("Wrong Layer Type",
                                                   "The layer \"Parallel Unit Lines\" cannot be created or has the wrong format")
            return

        vpr = vector_layer.dataProvider()
        fields = [f.name() for f in vpr.fields().toList()]
        if not "name" in fields:
            vpr.addAttributes([QgsField("name", QVariant.String, len=255)])

        name_field_index = vpr.fields().indexOf("name")
        if vpr.fields()[name_field_index].typeName().lower() != "string":
            self.__iface.messageBar().pushCritical("Wrong Attribute Type",
                                                   "The name attribute of the layer \"Parallel Unit Lines\" is not of type \"String\"!")
            return

        try:
            QgsMessageLog.logMessage("Adding units to the layer [{}]".format(len(unit_list)), level=0)
            # adding the features to the layer
            for unit in unit_list:
                f = QgsFeature()
                # unit = QgsRubberBand()
                f.setGeometry(unit[1])
                # f.setAttribute(name_field_index, unit[0])
                attr = list()
                for field in vpr.fields().toList():
                    attr.append(None)
                attr[name_field_index] = unit[0]
                f.setAttributes(attr)
                QgsMessageLog.logMessage("Adding unit \"{}\" - id: {} / fid: {}".format(unit[0], name_field_index, f.id()), level=0)
                vpr.addFeatures([f])
                #vpr.changeAttributeValues({f.id(): attr})

            QgsMessageLog.logMessage("Through the list without error...", level=0)

            vector_layer.updateExtents()
        except Exception as e:
            _, _, exc_traceback = sys.exc_info()
            text = "Error Message:\n{}\nTraceback:\n{}".format(str(e), '\n'.join(traceback.format_tb(exc_traceback)))
            # text = "Error Message:\nNone\nTraceback:\n{}".format(traceback.print_exc())
            QgsMessageLog.logMessage(text, level=2)
            #QgsMessageLog.logMessage("An exception occurred:\n{}".format(str(e)), level=2)
        finally:
            QgsMessageLog.logMessage("Finished adding units", level=0)
            self.reset()

    def reset(self) -> None:
        """
        Resets the object to the initialization stage
        :return: Nothing
        """
        self.__active_geometry = None
        self.__active_line = None
        self.__line_normal = None
        self.__side = 1
        self.__dockwidget.start_construction.setEnabled(False)

        self.__reset_tmp_units()
