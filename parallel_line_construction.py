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
from PyQt5.QtWidgets import QAction, QFileDialog, QHeaderView
from qgis.core import QgsMapLayer, QgsMessageLog, QgsProject, QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint

from .LineConstruction import LineConstruction
from .HorizonConstruct import HorizonConstructData, HorizonConstructDelegate, HorizonConstructModel
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

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/parallel_line_construction/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'ParallelLine Construction'),
            callback=self.run,
            parent=self.iface.mainWindow())

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING ParallelLineConstruction"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
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

            self.dockwidget.add_unit.clicked.connect(self.add_unit)
            self.dockwidget.remove_unit.clicked.connect(self.remove_unit)
            self.dockwidget.move_unit_up.clicked.connect(self.move_unit_up)
            self.dockwidget.move_unit_down.clicked.connect(self.move_unit_down)
            self.dockwidget.load_unit_table.clicked.connect(self.load_unit_table)
            self.dockwidget.save_unit_table.clicked.connect(self.save_unit_table)
            self.dockwidget.start_construction.clicked.connect(self.start_line_construction)

            try:
                # noinspection PyCallByClass,PyArgumentList
                QgsMessageLog.logMessage("\n\n{}\n\n".format(100 * "="), level=0)
                data = list()
                data.append(HorizonConstructData(True, False, "mo", 70, QColor(10, 255, 20)))
                data.append(HorizonConstructData(True, False, "mm", 110, QColor(10, 150, 20)))
                data.append(HorizonConstructData(True, True, "mu", 100, QColor(10, 100, 20)))
                data.append(HorizonConstructData(True, False, "so", 150, QColor(255, 255, 20)))

                self.__model = HorizonConstructModel(data)
                self.__line_construct.model = self.__model
                self.dockwidget.table_view.setModel(self.__model)
                self.dockwidget.table_view.setItemDelegate(HorizonConstructDelegate())
                self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            except Exception as e:
                self.exception_handling(e)

            # set active_layer and run slot once at plugin start
            self.iface.currentLayerChanged.connect(self.on_current_layer_changed)
            self.__active_layer = self.iface.activeLayer()
            self.on_current_layer_changed(self.__active_layer)

    def exception_handling(self, e: Exception) -> None:
        _, _, exc_traceback = sys.exc_info()
        text = "Error Message:\n{}\nTraceback:\n{}".format(str(e), '\n'.join(traceback.format_tb(exc_traceback)))
        self.iface.messageBar().pushMessage("Error",
                                            "An exception occurred during the process. " +
                                            "For more details, please take a look to the log windows.",
                                            level=2)

        # noinspection PyCallByClass,PyArgumentList
        QgsMessageLog.logMessage(text, level=2)

    def add_unit(self) -> None:
        self.__model.insertRow(self.__model.rowCount(), HorizonConstructData())

    def remove_unit(self) -> None:
        # table = QTableView()
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.removeRow(row)

    def move_unit_down(self) -> None:
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.moveRowDown(row)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def move_unit_up(self) -> None:
        selection = self.dockwidget.table_view.selectionModel()
        if not selection.hasSelection():
            return

        row = selection.selectedIndexes()[0].row()
        self.__model.moveRowUp(row)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dockwidget.table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def load_unit_table(self):
        # noinspection PyArgumentList
        file = QFileDialog.getOpenFileName(self.dockwidget, "Save to", QgsProject.instance().readPath("./"),
                                           "JSON file (*.json);;All(*)")
        file = file[0]
        with open(file) as data_file:
            data_loaded = json.load(data_file)

        # parsing the data
        model_data = list()
        try:
            keys = list(data_loaded.keys())
            keys.sort()
            for i in keys:
                data = HorizonConstructData()
                for j in data_loaded[i]:
                    index = HorizonConstructData.get_header_index(j)
                    if index == -1:
                        raise ValueError("Unknown key: {}".format(str(j)))
                    if j == "color":
                        data_loaded[i][j] = QColor(data_loaded[i][j])
                    data[index] = data_loaded[i][j]
                model_data.append(data)

        except Exception as e:
            self.exception_handling(e)
            return

        for i in range(self.__model.rowCount()):
            self.__model.removeRow(0)

        for item in model_data:
            self.__model.insertRow(self.__model.rowCount(), item)

    def save_unit_table(self):
        # noinspection PyArgumentList
        file = QFileDialog.getSaveFileName(self.dockwidget, "Save to", QgsProject.instance().readPath("./"),
                                           "JSON file (*.json);;All(*)")
        file = file[0]
        if file != "":
            out_dict = dict()
            for i in range(self.__model.rowCount()):
                out_dict[i] = dict()
                for j in range(self.__model.columnCount()):
                    name = HorizonConstructData.get_header_name(j)
                    index = self.__model.index(i, j)
                    out_dict[i][name] = index.data(Qt.DisplayRole)
                    if j == 4:
                        out_dict[i][name] = out_dict[i][name].name()
            with io.open(file, 'w', encoding='utf8') as outfile:
                json_data = json.dumps(out_dict, indent=2, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
                outfile.write(json_data)

    def on_current_layer_changed(self, map_layer: QgsMapLayer) -> None:
        if self.__active_layer is not None:
            # noinspection PyBroadException
            try:
                self.__active_layer.selectionChanged.disconnect()
            except:
                pass
        self.__active_layer = map_layer

        if (self.__active_layer is None) or (self.__active_layer.type() != QgsMapLayer.VectorLayer):
            return

        self.__active_layer.selectionChanged.connect(self.on_active_layer_selection_changed)
        self.parse_selection()

    def on_active_layer_selection_changed(self):
        self.parse_selection()

    def parse_selection(self):
        self.dockwidget.notifications.setText("")
        if self.__active_layer is None:
            self.dockwidget.start_construction.setEnabled(False)

        # noinspection PyArgumentList
        geometry_type = QgsWkbTypes.geometryDisplayString(self.__active_layer.geometryType())
        selected_features = self.__active_layer.selectedFeatures()

        if len(selected_features) == 0 or geometry_type != "Line":
            self.__line_construct.reset()
            self.dockwidget.start_construction.setEnabled(False)
            self.dockwidget.construct.setEnabled(False)
            return

        text = ""

        # noinspection PyArgumentList
        if QgsWkbTypes.isMultiType(self.iface.activeLayer().wkbType()):
            text += "This is line is stored as a multi part line. This tool only uses the first part, if more than " + \
                    "one exists!\n\n"

        if len(selected_features) > 1:
            text += "Multiple features selected. Using only the first of this selection.\n\n"

        self.__line_construct.active_geometry = selected_features[0].geometry()

        if self.__line_construct.active_geometry.isEmpty():
            self.dockwidget.notifications.setText("Selected an empty geometry!")
            self.__line_construct.reset()
            return

        if self.__line_construct.active_geometry.isMultipart():
            self.__line_construct.active_geometry = self.__line_construct.active_geometry.asGeometryCollection()[0]

        line = self.__line_construct.active_geometry.asPolyline()
        if len(line) < 2:
            self.dockwidget.notifications.setText("Selected line has less than two points. Cannot use it.")
            self.__line_construct.reset()
            return

        self.__line_construct.active_line = line

        self.dockwidget.start_construction.setEnabled(True)
        self.dockwidget.notifications.setText(text)

    def start_line_construction(self):
        try:
            self.__previous_map_tool = self.iface.mapCanvas().mapTool()
            self.__my_map_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            self.__my_map_tool.canvasClicked.connect(self.manage_click)
            self.iface.mapCanvas().setMapTool(self.__my_map_tool)
            self.iface.mapCanvas().xyCoordinates.connect(self.update_coordinates)
        except Exception as e:
            self.exception_handling(e)

    def update_coordinates(self, pos):
        text = "X: {:0.2f} - Y: {:0.2f}\n".format(pos.x(), pos.y())
        self.dockwidget.notifications.setText(text)
        self.__line_construct.calc_side(pos)

    def manage_click(self, pos, clicked_button):
        if clicked_button == Qt.LeftButton:
            self.__line_construct.calc_side(pos)
            self.dockwidget.notifications.setText(
                "Clicked on\nX: {:0.2f}\nY: {:0.2f}\nside: {}".format(pos.x(), pos.y(), self.__line_construct.side))

        if clicked_button == Qt.RightButton:
            self.__line_construct.side = 0
            self.dockwidget.notifications.setText("Nothing changed")
        # reset to the previous mapTool
        self.iface.mapCanvas().setMapTool(self.__previous_map_tool)
        # clean remove myMapTool and relative handlers
        self.__my_map_tool = None
        self.iface.mapCanvas().xyCoordinates.disconnect(self.update_coordinates)

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
