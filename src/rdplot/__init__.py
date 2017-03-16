#!/usr/bin/python3
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QItemSelectionModel, QSize
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from os.path import sep, isfile, isdir
from os import path

import jsonpickle
import pkg_resources

import sys
here = path.abspath(path.dirname(__file__))
sys.path.append(here)

from PlotWidget import PlotWidget
from SimulationDataItem import dict_tree_from_sim_data_items
from model import SimDataItemTreeModel, OrderedDictModel, VariableTreeModel, BdTableModel
from view import QRecursiveSelectionModel

Ui_name = pkg_resources.resource_filename(__name__, 'ui' + sep + 'mainWindow.ui')
Ui_MainWindow, QMainWindow = loadUiType(Ui_name)

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

        # Connect signals of menus
        self.actionOpen_File.triggered.connect(
            self.simDataItemTreeView.add_sim_data_item
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

        self.actionSave_Data.triggered.connect(
            self.save_current_selection
        )

        self.actionLoad_Data.triggered.connect(
            self.load_rd_data
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
        self._variable_tree_selection_model.selectionChanged.disconnect()
        self.simDataItemTreeModel.remove(list(values))
        self._variable_tree_selection_model.selectionChanged.connect(self.update_plot)


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
        # Note, that overwriting only issues one `updated` signal, and thus,
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
        self.variableTreeView.expandToDepth(1)

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
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table as', '.', 'tex')
        filename = ''.join(filename)
        if not len(filename) == 0:
            self.bdTableModel.export_to_latex(filename)

    def on_combo_box(self):
        # just update the bd table but do not change the anchor
        self.update_bd_table(-1)

    def save_current_selection(self):
        """Saves the current selected sim data item collection"""
        if not self.get_selected_simulation_data_items():
            msg = QMessageBox(self)  # use self as parent here
            msg.setIcon(QMessageBox.Information)
            msg.setText("You did not select any simualtion data item to store\n"
                        "Please make a selection and try again.")
            msg.setWindowTitle("Info")
            msg.show()
            return
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save RD data as', '.', '*.rd')
        filename = filename[0] + filename[1][1:]
        if not len(filename) == 0:
            f = open(filename, 'w')
            f.write(jsonpickle.encode(self.get_selected_simulation_data_items()))
            f.close()

    def load_rd_data(self):
        """Loads rd data from file"""
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Load RD data', '.', '*.rd')[0]
        if not len(filename) == 0:
            f = open(filename, 'r')
            json_str = f.read()
            sim_data_items = jsonpickle.decode(json_str)
            self.simDataItemTreeModel.update(sim_data_items)
            f.close()

    def process_cmd_line_args(self, args):
        """Processes cmd line arguments. Those are only pathes or files."""
        for path in args[1:]:
            if not isdir(path) and not isfile(path):
                continue
            if path.endswith('.rd'):
                f = open(path, 'r')
                json_str = f.read()
                sim_data_items = jsonpickle.decode(json_str)
                self.simDataItemTreeModel.update(sim_data_items)
                f.close()
                continue

            self.simDataItemTreeView.msg.show()
            self.simDataItemTreeView.parserThread.addPath(path)
            self.simDataItemTreeView.parserThread.start()


def main():

    app = QtWidgets.QApplication(sys.argv)

    # set icon of application
    app_icon = QtGui.QIcon()
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT1024.png'), QSize(1024, 1024))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT512.png'), QSize(512, 512))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT256.png'), QSize(256, 256))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT128.png'), QSize(128, 128))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT64.png'), QSize(64, 64))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT32.png'), QSize(32, 32))
    app_icon.addFile(pkg_resources.resource_filename(__name__,'logo/PLOT16.png'), QSize(16, 16))
    app.setWindowIcon(app_icon)

    main_window = Main()
    main_window.show()

    args = app.arguments()
    main_window.process_cmd_line_args(args)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

