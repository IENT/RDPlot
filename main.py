from PyQt5.uic import loadUiType
from PyQt5.QtCore import QItemSelectionModel

from matplotlib.figure import Figure

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from mpldatacursor import datacursor

import numpy as np
import math
from os.path import sep

from model import (SimDataItemTreeModel, OrderedDictModel,
                   VariableTreeModel, BdTableModel, dict_tree_from_sim_data_items)
from view import (QRecursiveSelectionModel)

Ui_MainWindow, QMainWindow = loadUiType('ui' + sep + 'mainWindow.ui')
Ui_PlotWidget, QWidget = loadUiType('ui' + sep + 'plotWidget.ui')


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        self.plotAreaVerticalLayout = QtWidgets.QVBoxLayout()
        self.plotsFrame.setLayout(self.plotAreaVerticalLayout)

        # add a widget for previewing plots, they can then be added to the actual plot
        self.plotPreview = PlotWidget()
        self.plotAreaVerticalLayout.addWidget(self.plotPreview)
        # Create tree model to store sim data items and connect it to views
        self.simDataItemTreeModel = SimDataItemTreeModel()
        self.bdTableModel = BdTableModel()
        self.simDataItemTreeView.setModel(self.simDataItemTreeModel)
        self.plotPreview.tableView.setModel(self.bdTableModel)

        # connect a double clicked section of the bd table to a change of the anchor
        self.plotPreview.tableView.horizontalHeader().sectionDoubleClicked.connect(self.update_bd_table)

        # Set custom selection model, so that sub items are automatically
        # selected if parent is selected
        self._selection_model = QRecursiveSelectionModel(self.simDataItemTreeView.model())
        self.simDataItemTreeView.setSelectionModel(self._selection_model)

        # Connect list view with model for the selected values of tree view
        self.selectedSimulationDataItemListModel = OrderedDictModel()
        self.simDataItemListView.setModel(self.selectedSimulationDataItemListModel)
        self._selection_model.selectionChanged.connect(self.change_list)

        # set up signals and slots
        self.selectedSimulationDataItemListModel.items_changed.connect(
            self.update_variable_tree
        )

        # Connect signals of menues
        self.actionOpen_File.triggered.connect(
            self.simDataItemTreeView.add_sim_data_item
        )
        self.actionOpen_Sequence.triggered.connect(
            self.simDataItemTreeView.add_sequence
        )
        self.actionOpen_Directory.triggered.connect(
            self.simDataItemTreeView.add_folder
        )
        self.actionHide_PlotSettings.triggered.connect(
            self.set_plot_settings_visibility
        )
        self.actionHide_Sequence.triggered.connect(
            self.set_sequence_widget_visibility
        )
        self.actionHide_Status.triggered.connect(
            self.set_status_widget_visibility
        )

        self.actionSave_Table.triggered.connect(
            self.save_bd_table
        )

        self.variableTreeModel = VariableTreeModel()
        self.variableTreeView.setModel(self.variableTreeModel)
        self.plotsettings.visibilityChanged.connect(self.plot_settings_visibility_changed)
        self.sequenceWidget.visibilityChanged.connect(self.sequence_widget_visibility_changed)
        self.statusWidget.visibilityChanged.connect(self.status_widget_visibility_changed)

        # Set recursive selection model for variable view
        self._variable_tree_selection_model = QRecursiveSelectionModel(
            self.variableTreeView.model()
        )
        self.variableTreeView.setSelectionModel(
            self._variable_tree_selection_model
        )

        # set up combo boxes for rate/psnr and interpolation options
        self.combo_interp.addItems(["pchip", "pol"])
        self.combo_rate_psnr.addItems(["drate", "dsnr"])
        self.combo_interp.currentIndexChanged.connect(self.on_combo_box)
        self.combo_rate_psnr.currentIndexChanged.connect(self.on_combo_box)

    # sets Visibility for the Plotsettings Widget
    def set_plot_settings_visibility(self):
        self.plotsettings.visibilityChanged.disconnect(self.plot_settings_visibility_changed)
        if self.plotsettings.isHidden():
            self.plotsettings.setVisible(True)
        else:
            self.plotsettings.setHidden(True)
        self.plotsettings.visibilityChanged.connect(self.plot_settings_visibility_changed)

    # updates the QAction if Visibility is changed
    def plot_settings_visibility_changed(self):
        if self.plotsettings.isHidden():
            self.actionHide_PlotSettings.setChecked(True)
        else:
            self.actionHide_PlotSettings.setChecked(False)
        self._variable_tree_selection_model.selectionChanged.connect(self.update_plot)

        self.simDataItemTreeView.deleteKey.connect(self.remove)

    # sets Visibility for the Sequence Widget
    def set_sequence_widget_visibility(self):
        self.sequenceWidget.visibilityChanged.disconnect(self.sequence_widget_visibility_changed)
        if self.sequenceWidget.isHidden():
            self.sequenceWidget.setVisible(True)
        else:
            self.sequenceWidget.setHidden(True)
        self.sequenceWidget.visibilityChanged.connect(self.sequence_widget_visibility_changed)

    def sequence_widget_visibility_changed(self):
        if self.sequenceWidget.isHidden():
            self.actionHide_Sequence.setChecked(True)
        else:
            self.actionHide_Sequence.setChecked(False)

    # Sets Visibility for the Status Widget
    def set_status_widget_visibility(self):
        self.statusWidget.visibilityChanged.disconnect(self.status_widget_visibility_changed)
        if self.statusWidget.isHidden():
            self.statusWidget.setVisible(True)
        else:
            self.statusWidget.setHidden(True)
        self.statusWidget.visibilityChanged.connect(self.status_widget_visibility_changed)

    def status_widget_visibility_changed(self):
        if self.statusWidget.isHidden():
            self.actionHide_Status.setChecked(True)
        else:
            self.actionHide_Status.setChecked(False)

    def remove(self):
        values = self.selectedSimulationDataItemListModel.values()
        # List call necessary to avoid runtime error because of elements changing
        # during iteration
        self.simDataItemTreeModel.remove(list(values))

    def change_list(self, q_selected, q_deselected):
        """Extend superclass behavior by automatically adding the values of
           all selected items in :param: `q_selected` to value list model. """

        selected_q_indexes = q_deselected.indexes()

        q_reselect_indexes = []
        for q_index in self.simDataItemTreeView.selectedIndexes():
            if q_index not in selected_q_indexes:
                q_reselect_indexes.append(q_index)

        # Find all all values that are contained by selected tree items
        tuples = []
        for q_index in q_selected.indexes() + q_reselect_indexes:
            # Add values, ie. sim data items stored at the item, to the list
            # model.
            sim_data_items = q_index.internalPointer().values
            tuples.extend((e.path, e) for e in sim_data_items)

        # Overwrite all elements in dictionary by selected values
        # Note, that ovrewriting only issues one `updated` signal, and thus,
        # only rerenders the plots one time. Therefore, simply overwriting
        # is much more efficient, despite it would seem, that selectively
        # overwriting keys is.
        self.selectedSimulationDataItemListModel.clear_and_update_from_tuples(tuples)

    def get_selected_simulation_data_items(self):
        return [self.selectedSimulationDataItemListModel[key] for key in self.selectedSimulationDataItemListModel]

    def get_plot_data_collection_from_selected_variables(self):
        """Get a :class: `dict` with y-variable as key and values as items
        from the current selection of the variable tree.

        :rtype: :class: `dict` of :class: `string` and :class: `list`
        """

        plot_data_collection = []
        for q_index in self.variableTreeView.selectedIndexes():
            item = q_index.internalPointer()
            if len(item.values) > 0:
                plot_data_collection.extend(item.values)

        return plot_data_collection

    def update_variable_tree(self):
        """Collect all SimDataItems currently selected, and create variable
        tree and corresponding data from it. Additionaly reselect all prevously
        selected variables.
        """

        # Create a list of all currently selected paths
        # Note, that *q_index* can not be used directly, because it might
        # change if the variable tree is recreated
        selected_path_collection = []
        for q_index in self.variableTreeView.selectedIndexes():
            selected_path_collection.append(
                # Create list of identifiers from path
                # Note, that the root node is excluded from the path
                [item.identifier for item in q_index.internalPointer().path[1:]]
            )

        # Join the data of all currently selected items to a dictionary
        # tree
        sim_data_items = self.get_selected_simulation_data_items()
        dict_tree = dict_tree_from_sim_data_items(sim_data_items)
        # Reset variable tree and update it with *dict_tree*
        self.variableTreeModel.clear_and_update_from_dict_tree(dict_tree)

        # Auto expand variable tree
        self.variableTreeView.expandAll()

        # Reselect all variables, which also exist on the new tree
        for path in selected_path_collection:
            # Try to reselect, and do nothing, if path does not exist anymore
            try:
                # Reselect new item corresponding to the previously selected
                # path
                item = self.variableTreeModel.get_item_from_path(*path)
                self.variableTreeView.selectionModel().select(
                    self.variableTreeModel._get_index_from_item(item),
                    QItemSelectionModel.Select,
                )
            except KeyError:
                pass

    # updates the plot if the plot variable is changed
    def update_plot(self):
        plot_data_collection = self.get_plot_data_collection_from_selected_variables()

        self.plotPreview.change_plot(plot_data_collection)

        # update the model for the bd table, note the anchor is always
        # the first config if new simDataItems are selected
        self.bdTableModel.update(plot_data_collection, self.combo_rate_psnr.currentText(),
                                 self.combo_interp.currentText())

    def update_bd_table(self, index):

        # update bd table, the index determines the anchor,
        # if it is non integer per default the first config is regarded as
        # anchor
        self.bdTableModel.update_table(self.combo_rate_psnr.currentText(),
                                       self.combo_interp.currentText(), index)

    def save_bd_table(self):
        if self.bdTableModel.rowCount(self) == 0:
            return
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table as')[0]
        if not len(filename) == 0:
            self.bdTableModel.export_to_latex(filename)

    def on_combo_box(self):
        # just update the bd table but do not change the anchor
        self.update_bd_table(-1)

    def clear_plot(self):
        pass


class NestedDict(dict):
    """
    Provides the nested dict used to store all the sequence data.
    """

    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())


class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, ):
        super(PlotWidget, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        # set figure and backgroung to transparent
        self.plotAreaWidget.fig = Figure(facecolor="white")

        # set some properties for canvas
        self.plotAreaWidget.canvas = FigureCanvas(self.plotAreaWidget.fig)
        # self.plotAreaWidget.canvas.setParent(self.plotAreaWidget)
        # self.plotAreaWidget.canvas.setFocusPolicy(Qt.StrongFocus)

        # connect scroll and double click event to canvas
        self.plotAreaWidget.canvas.mpl_connect('scroll_event', self.on_wheel)
        self.plotAreaWidget.canvas.mpl_connect('button_press_event', self.on_db_click)

        self.verticalLayout_3.addWidget(self.plotAreaWidget.canvas)
        # add the toolbar for the plot
        self.toolbar = NavigationToolbar(self.plotAreaWidget.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.verticalLayout_3.addWidget(self.toolbar)

    # refreshes the figure according to new changes done
    def change_plot(self, plot_data_collection):
        """Plot all data from the *plot_data_collection*

        :param plot_data_collection: A iterable collection of :clas: `PlotData`
            objects, which should be plotted.
            temporal data
        """

        if len(plot_data_collection) == 0:
            return

        # put a subplot into the figure and set the margins a little bit tighter than the defaults
        # this is some workaround for PyQt similar to tight layout
        self.plotAreaWidget.fig.clear()
        axis = self.plotAreaWidget.fig.add_subplot(111)
        self.plotAreaWidget.fig.subplots_adjust(left=0.05, right=0.95,
                                                bottom=0.1, top=0.95,
                                                hspace=0.2, wspace=0.2)

        for plot_data in plot_data_collection:
            # Convert list of pairs of strings to two sorted lists of floats
            values = ((float(x), float(y)) for (x, y) in plot_data.values)
            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list(zip(*sorted_value_pairs))

            # Create legend from variable path and sim data items identifiers
            legend = " ".join([plot_data.identifiers[0].split('_')[0]] + [plot_data.identifiers[1]] + plot_data.path)

            # plot the current plotdata and set the legend
            curve = axis.plot(xs, ys, '-x', label=legend)
            axis.legend(loc='lower right')

            # add datacurser for the curve
            datacursor(curve)

            # set grid and default y tick in 0.5 spacing
            axis.grid(True)
            start, end = axis.get_ylim()
            start = math.floor(start)
            end = math.ceil(end)
            axis.yaxis.set_ticks(np.arange(start, end, 0.5))

            self.plotAreaWidget.canvas.draw()

    # this function enables zoom with mousewheel
    # see also: http://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
    def on_wheel(self, event):
        base_scale = 1.2
        axis = self.plotAreaWidget.fig.gca()
        if not axis.has_data():
            axis.remove()
            return
        # get the current x and y limits
        cur_xlim = axis.get_xlim()
        cur_ylim = axis.get_ylim()
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            return

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        rel_x = (cur_xlim[1] - event.xdata) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (cur_ylim[1] - event.ydata) / (cur_ylim[1] - cur_ylim[0])

        axis.set_xlim([event.xdata - new_width * (1 - rel_x),
                          event.xdata + new_width * rel_x])
        axis.set_ylim([event.ydata - new_height * (1 - rel_y),
                          event.ydata + new_height * rel_y])

        self.plotAreaWidget.canvas.draw()  # force re-draw

    def on_db_click(self, event):
        if event.dblclick:
            axis = self.plotAreaWidget.fig.gca()
            if not axis.has_data():
                axis.remove()
                return
            axis.autoscale()
            self.plotAreaWidget.canvas.draw()  # force re-draw
        else:
            return


if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
