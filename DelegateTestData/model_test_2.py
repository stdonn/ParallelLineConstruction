# -*- coding: utf-8 -*-

from PyQt5.QtCore import QModelIndex, QPoint, QSize
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QListView, QStyle, QStyledItemDelegate, \
    QStyleOptionViewItem

import sys

from DelegateTestData.HorizonConstructData import HorizonConstructData
from DelegateTestData.HorizonConstructModel import HorizonConstructModel
from DelegateTestData.thickness_table_entry import ThicknessTableEntry


class HorizonConstructDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(HorizonConstructDelegate, self).__init__(*args, **kwargs)
        self.my_thickness_table_entry = ThicknessTableEntry(HorizonConstructData())

    def paint(self, painter, option, index):
        index_data = index.data()
        # print("{} - {}".format(index_data, str(type(index_data))))
        if isinstance(index_data, HorizonConstructData):
            self.my_thickness_table_entry.set_data(index_data)
            if option.state & QStyle.State_Selected:
                self.my_thickness_table_entry.setStyleSheet(
                    "background: #B2D7FF".format(option.palette.highlight().color().name()))
            else:
                self.my_thickness_table_entry.setStyleSheet(
                    "background: {}".format(option.palette.window().color().name()))

            width = self.my_thickness_table_entry.sizeHint().width()
            width = width if painter.device().width() < width else painter.device().width()
            self.my_thickness_table_entry.setFixedWidth(width)
            self.my_thickness_table_entry.render(painter,
                                                 QPoint(0, index.row() * self.my_thickness_table_entry.size().height()))

        # if isinstance(index_data, bool):
        #
        # if isinstance(index_data, bool):
        #    if option.state & QStyle.State_Selected:
        #        painter.fillRect(option.rect, option.palette.highlight())

        #    starRating.paint(painter, option.rect, option.palette,
        #            StarRating.ReadOnly)
        else:
            super(HorizonConstructDelegate, self).paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        # print(str(self.my_thickness_table_entry.sizeHint()))
        # return self.my_thickness_table_entry.sizeHint()
        return QSize(240, 31)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = list()
    data.append(HorizonConstructData(True, False, "mo", 70, QColor(10, 255, 20, 0)))
    data.append(HorizonConstructData(True, False, "mm", 100, QColor(10, 150, 20, 0)))
    data.append(HorizonConstructData(True, False, "msadfsdfsdfsd fsdfsfsfsdfu", 110, QColor(10, 100, 20, 0)))
    data.append(HorizonConstructData(True, False, "so", 150, QColor(255, 255, 20, 0)))

    model = HorizonConstructModel(data)

    tableView = QListView()
    tableView.setModel(model)
    tableView.setItemDelegate(HorizonConstructDelegate())
    tableView.setEditTriggers(
        QAbstractItemView.DoubleClicked |
        QAbstractItemView.SelectedClicked)
    tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
    # tableView.setMinimumSize(240, 4 * 31)
    # tableView.setMaximumSize(240, 4 * 31)
    tableView.show()

    sys.exit(app.exec_())
