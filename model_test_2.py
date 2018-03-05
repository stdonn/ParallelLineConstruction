# -*- coding: utf-8 -*-

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QTableView, QStyledItemDelegate

import sys

from HorizonConstructData import HorizonConstructData
from HorizonConstructModel import HorizonConstructModel


class HorizonConstructDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        index_data = index.data()
        print("{} - {}".format(index_data, str(type(index_data))))
        #if isinstance(index_data, bool):
        #
        #if isinstance(index_data, bool):
        #    if option.state & QStyle.State_Selected:
        #        painter.fillRect(option.rect, option.palette.highlight())

        #    starRating.paint(painter, option.rect, option.palette,
        #            StarRating.ReadOnly)
        #else:
        super(HorizonConstructDelegate, self).paint(painter, option, index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = list()
    data.append(HorizonConstructData(True, False, "mo", 70, QColor(10, 255, 20, 0)))
    data.append(HorizonConstructData(True, False, "mm", 100, QColor(10, 150, 20, 0)))
    data.append(HorizonConstructData(True, False, "mu", 110, QColor(10, 100, 20, 0)))
    data.append(HorizonConstructData(True, False, "so", 150, QColor(255, 255, 20, 0)))

    model = HorizonConstructModel(data)

    tableView = QTableView()
    tableView.setModel(model)
    tableView.setItemDelegate(HorizonConstructDelegate())
    tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
    tableView.show()

    sys.exit(app.exec_())
