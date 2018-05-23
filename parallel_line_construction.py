# -*- coding: utf-8 -*-
"""
QGIS plugin: ParallelLineConstruction

This plugin constructs parallel lines based on a given base line

copyright            : (C) 2018 by Stephan Donndorf
email                : stephan@donndorf.info

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import io
import json
import os.path
import sys
import traceback

from PyQt5.QtCore import QCoreApplication, QSettings, QTranslator, Qt, qVersion
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QAction, QFileDialog, QHeaderView, QPushButton
from qgis.core import QgsGeometry, QgsMapLayer, QgsMessageLog, QgsPoint, QgsProject, QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint

from .HorizonConstruct import UnitConstructionData, UnitConstructionDelegate, UnitConstructionModel
from .LineConstruction import LineConstruction
from .parallel_line_construction_dockwidget import ParallelLineConstructionDockWidget
# Initialize Qt resources from file resources.py
# noinspection PyUnresolvedReferences
from .resources import *


class ParallelLineConstruction:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ParallelLineConstruction_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Parallel Line Construction')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ParallelLineConstruction')
        self.toolbar.setObjectName(u'ParallelLineConstruction')

        # print "** INITIALIZING ParallelLineConstruction"

        self.pluginIsActive = False
        self.dockwidget = None
        self.__my_map_tool = None
        self.__previous_map_tool = None
        self.__model = None
        self.__active_layer = None
        self.__line_construct = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ParallelLineConstruction', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    # noinspection PyPep8Naming
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/parallel_line_construction/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'ParallelLine Construction'),
            callback=self.run,
            parent=self.iface.mainWindow())

    # --------------------------------------------------------------------------

    # noinspection PyPep8Naming
    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING ParallelLineConstruction"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crash
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD ParallelLineConstruction"

        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Parallel Line Construction'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        try:
            del self.toolbar
            self.__line_construct.reset()
        except AttributeError:
            pass

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING ParallelLineConstruction"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = ParallelLineConstructionDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            self.__line_construct = LineConstruction(self.iface, self.dockwidget)
            self.dockwidget.line_join_style.addItems(["Use rounded joins", "Use mitered joins", "Use beveled joins"])
            self.dockwidget.line_join_style.setCurrentIndex(1)

            self.dockwidget.add_unit.clicked.connect(self.on_add_unit_clicked)
            self.dockwidget.remove_unit.clicked.connect(self.on_remove_unit_clicked)
            self.dockwidget.move_unit_up.clicked.connect(self.on_move_unit_up_clicked)
            self.dockwidget.move_unit_down.clicked.connect(self.on_move_unit_down_clicked)
            self.dockwidget.load_unit_table.clicked.connect(self.on_load_unit_table_clicked)
            self.dockwidget.save_unit_table.clicked.connect(self.on_save_unit_table_clicked)
            self.dockwidget.start_construction.clicked.connect(self.on_start_line_construction_clicked)

            try:
                self.__model = UnitConstructionModel()
                self.__line_construct.model = self.__model
                self.dockwidget.table_view.setModel(self.__model)
                self.dockwidget.table_view.setItemDelegate(UnitConstructionDelegate())
                self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            except Exception as e:
                self._exception_handling(e)

            # set active_layer and run slot once at plugin start
            self.iface.currentLayerChanged.connect(self.on_current_layer_changed)
            self.__active_layer = self.iface.activeLayer()
            self.on_current_layer_changed(self.__active_layer)

    #
    # user functions
    # --------------
    #
    # protected functions
    #
    def _exception_handling(self, e: Exception) -> None:
        """
        write the exception data to the QGIS message bar and message log
        :param e: Exception data
        :return: Nothing
        """
        _, _, exc_traceback = sys.exc_info()
        text = "Error Message:\n{}\nTraceback:\n{}".format(str(e), '\n'.join(traceback.format_tb(exc_traceback)))

        widget = self.iface.messageBar().createMessage("Error", "An exception occurred during the process. " +
                                                       "For more details, please take a look to the log windows.")
        button = QPushButton(widget)
        button.setText("Show log windows")
        # noinspection PyUnresolvedReferences
        button.pressed.connect(self.iface.openMessageLog)
        widget.layout().addWidget(button)
        self.iface.messageBar().pushWidget(widget, level = 2)

        # noinspection PyCallByClass,PyArgumentList,PyTypeChecker
        QgsMessageLog.logMessage(text, level=2)

    def _parse_selection(self):
        """
        parse the current selection inside the QGIS map and update the LineConstruction object and enable / disable
        the dockwidget.start_construction button
        :return: Nothing
        """
        if self.__active_layer is None:
            self.__line_construct.reset()
            return

        # noinspection PyArgumentList
        geometry_type = QgsWkbTypes.geometryDisplayString(self.__active_layer.geometryType())
        selected_features = self.__active_layer.selectedFeatures()

        if len(selected_features) == 0 or geometry_type != "Line":
            self.__line_construct.reset()
            return

        text = ""

        # noinspection PyArgumentList
        if QgsWkbTypes.isMultiType(self.iface.activeLayer().wkbType()):
            text += "This is line is stored as a multi part line. This tool only uses the first part, if more than " + \
                    "one exists!"

        if len(selected_features) > 1:
            if text != "":
                text += "\n\n"
            text += "Multiple features selected. Using only the first of this selection."

        self.__line_construct.active_feature_id = selected_features[0].id()
        self.__line_construct.active_geometry = selected_features[0].geometry()

        if self.__line_construct.active_geometry.isEmpty():
            self.iface.messageBar().pushWarning("Warning", "Selected an empty geometry!")
            self.__line_construct.reset()
            return

        if self.__line_construct.active_geometry.isMultipart():
            self.__line_construct.active_geometry = self.__line_construct.active_geometry.asGeometryCollection()[0]

        line = self.__line_construct.active_geometry.asPolyline()
        if len(line) < 2:
            self.iface.messageBar().pushWarning("Warning", "Selected line has less than two points. Cannot use it.")
            self.__line_construct.reset()
            return

        self.__line_construct.active_line = line

        self.dockwidget.start_construction.setEnabled(True)
        if text != "":
            self.iface.messageBar().pushInfo("Info: ", text)

    #
    # slots
    #
    def on_active_layer_selection_changed(self) -> None:
        """
        slot for recognizing selection changes on the active layer
        :return: Nothing
        """
        self._parse_selection()

    def on_add_unit_clicked(self) -> None:
        """
        Add a new unit to the model
        :return: Nothing
        """
        self.__model.insertRow(self.__model.rowCount(), UnitConstructionData())

    def on_current_layer_changed(self, map_layer: QgsMapLayer) -> None:
        """
        slot for checking selection changes
        :param map_layer:
        :return: Nothing
        """
        if self.__active_layer is not None:
            try:
                self.__active_layer.geometryChanged.disconnect(self.on_geometry_changed)
                self.__active_layer.selectionChanged.disconnect(self.on_active_layer_selection_changed)
            except AttributeError:
                pass

        if (map_layer is None) or (map_layer.type() != QgsMapLayer.VectorLayer):
            self.__active_layer = None
        else:
            self.__active_layer = map_layer
            self.__active_layer.geometryChanged.connect(self.on_geometry_changed)
            self.__active_layer.selectionChanged.connect(self.on_active_layer_selection_changed)

        self._parse_selection()

    def on_geometry_changed(self, fid: int, geometry: QgsGeometry) -> None:
        """
        Slot activated, if a geometry changed in an edit session of the currently selected active layer
        :param fid: FeatureID of the changed geometry
        :param geometry: changed QgsGeometry object
        :return: Nothing
        """
        # noinspection PyCallByClass,PyArgumentList,PyTypeChecker
        QgsMessageLog.logMessage("on_geometry_changed [{}]: {}".format(fid, str(geometry.asJson())), level=0)

        if self.__line_construct.active_feature_id == fid:
            # -> last part of self._parse_selection
            self.__line_construct.active_geometry = geometry

            if self.__line_construct.active_geometry.isEmpty():
                self.iface.messageBar().pushWarning("Warning", "Selected an empty geometry!")
                self.__line_construct.reset()
                return

            if self.__line_construct.active_geometry.isMultipart():
                self.__line_construct.active_geometry = self.__line_construct.active_geometry.asGeometryCollection()[0]

            line = self.__line_construct.active_geometry.asPolyline()
            if len(line) < 2:
                self.iface.messageBar().pushWarning("Warning", "Selected line has less than two points. Cannot use it.")
                self.__line_construct.reset()
                return

            self.__line_construct.active_line = line

    def on_move_unit_down_clicked(self) -> None:
        """
        slot for moving the unit selected in the view down in the model, if possible
        :return: Nothing
        """
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.move_row_down(row)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def on_move_unit_up_clicked(self) -> None:
        """
        slot for moving the unit selected in the view up in the model, if possible
        :return: Nothing
        """
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.move_row_up(row)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def on_load_unit_table_clicked(self) -> None:
        """
        Slot for loading the UnitConstructionModel from a text file in JSON format.
        :return: Nothing
        """
        # noinspection PyArgumentList
        file = QFileDialog.getOpenFileName(self.dockwidget, "Save to", QgsProject.instance().readPath("./"),
                                           "JSON file (*.json);;All(*)")
        file = file[0]
        with open(file) as data_file:
            data_loaded = json.load(data_file)

        # parsing the data
        model_data = list()
        try:
            keys = [int(i) for i in list(data_loaded.keys())]
            # noinspection PyCallByClass,PyArgumentList,PyTypeChecker
            #QgsMessageLog.logMessage("keys: {}".format(str(keys)), level=0)
            keys.sort()
            #QgsMessageLog.logMessage("keys sorted: {}".format(str(keys)), level=0)
            for i in keys:
                i = str(i)
                data = UnitConstructionData()
                for j in data_loaded[i]:
                    index = UnitConstructionData.get_header_index(j)
                    if index == -1:
                        raise ValueError("Unknown key: {}".format(str(j)))
                    if j == "color":
                        data_loaded[i][j] = QColor(data_loaded[i][j])
                    data[index] = data_loaded[i][j]
                model_data.append(data)

        except Exception as e:
            self._exception_handling(e)
            return

        for i in range(self.__model.rowCount()):
            self.__model.removeRow(0)

        for item in model_data:
            self.__model.insertRow(self.__model.rowCount(), item)

    def on_manage_click(self, pos: QgsPoint, clicked_button: int) -> None:
        """
        slot for processing a mouse click on the canvas if the QgsMapToolEmitPoint is active.
        Resets the map tool to the previous one
        :param pos: current mouse position
        :param clicked_button:
        :return: Nothing
        """
        if clicked_button == Qt.LeftButton:
            self.__line_construct.calc_side(pos)

        if clicked_button == Qt.RightButton:
            self.__line_construct.side = 0
        # reset to the previous mapTool
        self.iface.mapCanvas().setMapTool(self.__previous_map_tool)
        # clean remove myMapTool and relative handlers
        self.__my_map_tool = None
        self.iface.mapCanvas().xyCoordinates.disconnect(self.on_update_coordinates)

    def on_remove_unit_clicked(self) -> None:
        """
        Remove the unit data from the model of the selected index in the view
        :return: Nothing
        """
        # table = QTableView()
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.removeRow(row)

    def on_save_unit_table_clicked(self) -> None:
        """
        Slot for saving the current UnitConstructionModel into a text file in JSON format.
        :return: Nothing
        """
        # noinspection PyArgumentList
        file = QFileDialog.getSaveFileName(self.dockwidget, "Save to", QgsProject.instance().readPath("./"),
                                           "JSON file (*.json);;All(*)")
        file = file[0]
        if file != "":
            out_dict = dict()
            for i in range(self.__model.rowCount()):
                out_dict[i] = dict()
                for j in range(self.__model.columnCount()):
                    name = UnitConstructionData.get_header_name(j)
                    index = self.__model.index(i, j)
                    out_dict[i][name] = index.data(Qt.DisplayRole)
                    if j == 4:
                        out_dict[i][name] = out_dict[i][name].name()
            with io.open(file, 'w', encoding='utf8') as outfile:
                json_data = json.dumps(out_dict, indent=2, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
                outfile.write(json_data)

    def on_start_line_construction_clicked(self) -> None:
        """
        slot if the start line construction button clicked
        :return: Nothing
        """
        try:
            self.__previous_map_tool = self.iface.mapCanvas().mapTool()
            self.__my_map_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            # noinspection PyUnresolvedReferences
            self.__my_map_tool.canvasClicked.connect(self.on_manage_click)
            self.iface.mapCanvas().setMapTool(self.__my_map_tool)
            self.iface.mapCanvas().xyCoordinates.connect(self.on_update_coordinates)
        except Exception as e:
            self._exception_handling(e)

    def on_update_coordinates(self, pos: QgsPoint) -> None:
        """
        slot called, when mouse coordinates have been updated and a new side related to the line has to be calculated
        :param pos: current mouse position as QgsPoint
        :return: Nothing
        """
        self.__line_construct.calc_side(pos)

# Type information:
#
# geometryType = self.iface.activeLayer().geometryType()
# type = self.iface.activeLayer().wkbType()
# selected_features = self.active_layer.selectedFeatures()
#
# text = "{}\n".format(self.iface.activeLayer().name())
# text += "GeometryType: {}\n".format(QgsWkbTypes.geometryDisplayString(geometryType))
# text += "WkbType: {}\n".format(QgsWkbTypes.displayString(type))
# text += "hasZ:{} / hasM: {}\n".format(QgsWkbTypes.hasZ(type), QgsWkbTypes.hasM(type))
# text += "isMultiType:{} / isSingleType: {}\n".format(QgsWkbTypes.isMultiType(type), QgsWkbTypes.isSingleType(type))
# text += "Got {} selected features".format(len(selected_features))
# text += "\nJSON-Geometry:\n\n{}".format(self.active_line_feature.geometry().asJson())
