from os import path
from os.path import sep, isfile, isdir
from os import listdir
import csv
import cProfile, pstats

import pkg_resources
import jsonpickle
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QItemSelectionModel, QItemSelection, QSettings, QFileSystemWatcher, QTimer
from PyQt5.uic import loadUiType
from PyQt5.Qt import Qt


from rdplot.SimulationDataItem import dict_tree_from_sim_data_items, PlotData
from rdplot.Widgets.PlotWidget import PlotWidget
from rdplot.model import SimDataItemTreeModel, OrderedDictModel, VariableTreeModel, BdTableModel, BdUserGeneratedCurvesTableModel
from rdplot.view import QRecursiveSelectionModel

Ui_name = pkg_resources.resource_filename('rdplot', 'ui' + sep + 'mainWindow.ui')
Ui_MainWindow, QMainWindow = loadUiType(Ui_name)

here = pkg_resources.resource_filename('rdplot','')
#here = path.abspath(path.dirname(__file__) + '/../')

def do_cprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            stats = pstats.Stats(profile).sort_stats('cumtime')
            stats.dump_stats('remove_items_new.profile')
    return profiled_func

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        self.tabWidget.setCurrentIndex(0)

        self.plotAreaVerticalLayout = QtWidgets.QVBoxLayout()
        self.plotsFrame.setLayout(self.plotAreaVerticalLayout)

        #initialize Table
        self.headerV = self.tableWidget.verticalHeader()
        self.headerV.show()

        # add a widget for previewing plots, they can then be added to the actual plot
        self.plotPreview = PlotWidget()
        self.plotAreaVerticalLayout.addWidget(self.plotPreview)

        # Create tree model to store sim data items and connect it to views
        self.simDataItemTreeModel = SimDataItemTreeModel()
        self.bdTableModel = BdTableModel()
        self.bdUserGeneratedTableModel = BdUserGeneratedCurvesTableModel()
        self.simDataItemTreeView.setModel(self.simDataItemTreeModel)
        self.plotPreview.tableView.setModel(self.bdTableModel)

        # connect a double clicked section of the bd table to a change of the anchor
        self.plotPreview.tableView.horizontalHeader().sectionDoubleClicked.connect(self.update_bd_table)
        self.plotPreview.tableView.verticalHeader().sectionDoubleClicked.connect(self.update_bd_user_generated_curves_table)

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
            self.simDataItemTreeView.add_file
        )
        self.actionOpen_Directory.triggered.connect(
            self.simDataItemTreeView.add_folder
        )
        self.actionOpen_Directory_List.triggered.connect(
            self.simDataItemTreeView.add_folder_list
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

        self.actionExport_Figure_as_Tikzpicture.triggered.connect(
            self.plotPreview.export_plot_tikz
        )

        self.actionExport_TableWidget.triggered.connect(
            self.export_table_to_csv
        )

        self.actionSave_Data.triggered.connect(
            self.save_current_selection
        )

        self.action_About.triggered.connect(
            self.open_about_page
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

        # set up bd plot checkbox
        self.checkBox_bdplot.stateChanged.connect(self.update_bd_plot)

        self.curveWidget.hide()
        self.curveListModel = OrderedDictModel()
        self.curveListView.setModel(self.curveListModel)
        self.curveListSelectionModel = QItemSelectionModel(self.curveListModel)
        self.curveListView.setSelectionModel(self.curveListSelectionModel)
        self.curveListView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.curveWidget.visibilityChanged.connect(self.curve_widget_visibility_changed)

        self.actionGenerate_curve.triggered.connect(self.generate_new_curve)
        self.actionRemove_items.triggered.connect(self.remove)
        self.actionReload_files.triggered.connect(self.reload_files)

        self.settings = QSettings()
        self.get_recent_files()
        self.simDataItemTreeView.itemsOpened.connect(self.add_recent_files)

        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.warning_file_change)
        self.watcher.directoryChanged.connect(self.warning_file_change)
        self.simDataItemTreeView.parserThread.newParsedData.connect(self.add_files_to_watcher)
        self.show_file_changed_message = True
        self.reset_timer = QTimer(self)
        self.reset_timer.setSingleShot(True)
        self.reset_timer.setInterval(15000)
        self.reset_timer.timeout.connect(self._reset_file_changed_message)

        self.simDataItemTreeView.customContextMenuRequested.connect(self.show_sequences_context_menu)
        # self.curveListView.actionCalculateBD.triggered.connect(self.bd_user_generated_curves)

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
        self.curveListSelectionModel.selectionChanged.connect(self.update_plot)
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

    def curve_widget_visibility_changed(self):
        if self.curveWidget.isHidden():
            self.curveListView.delete_key.disconnect()
        else:
            self.curveListView.delete_key.connect(self.remove_curves)

    def remove(self):
        values = self.selectedSimulationDataItemListModel.values()

        for value in values:
            self.watcher.removePath(value.path)
        # List call necessary to avoid runtime error because of elements changing
        # during iteration
        self._variable_tree_selection_model.selectionChanged.disconnect()
        # disconnect slot to avoid multiple function triggers by selectionChanged signal
        # not disconnecting slows program down significantly
        self._selection_model.selectionChanged.disconnect(self.change_list)
        self.simDataItemTreeModel.remove(list(values))
        self.change_list(QItemSelection(), QItemSelection())
        self._selection_model.selectionChanged.connect(self.change_list)
        self._variable_tree_selection_model.selectionChanged.connect(self.update_plot)
        if len(self.selectedSimulationDataItemListModel.values()) == 0:
            self.update_plot()

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
        tree and corresponding data from it. Additionaly reselect all previously
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
        # check if qp values are the same
        # self.check_qp(sim_data_items)

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

    # TODO: it might be that some log files do not have a QP value, therefore the check_qp method must be
    #       implemented in a way that these files are not affected
    # def check_qp(self, sim_data_items): # check if qp values are the same for each sequence
    #     if len(sim_data_items) < 2: return
    #     sim_data_items.sort(key=lambda item: (item.sequence))
    #
    #     qp_list,list = [],[]
    #     seq = sim_data_items[0].sequence
    #     config = sim_data_items[0].config
    #
    #     for item in sim_data_items:
    #         if ((seq == item.sequence) & (config == item.config)):
    #             list.append(item.qp)
    #         elif (seq == item.sequence): #same sequence different config
    #             config = item.config
    #             qp_list.append(list)
    #             list = []
    #             list.append(item.qp)
    #         else:  # different sequence
    #             seq = item.sequence
    #             config = item.config
    #             qp_list.append(list)
    #             if not(all(list == qp_list[0] for list in qp_list)):
    #                 QtWidgets.QMessageBox.warning(self, "Warning",
    #                                               "Be careful! You chose a sequence with different QP.")
    #                 return
    #             list, qp_list = [], []
    #             list.append(item.qp)
    #     qp_list.append(list)
    #
    #     if not(all(list == qp_list[0] for list in qp_list )):
    #         QtWidgets.QMessageBox.warning(self, "Warning",
    #                                         "Be careful! You chose a sequence with different QP.")

    def check_labels(self):
        selectionmodel = self.variableTreeView.selectionModel()
        selected = self.variableTreeView.selectedIndexes()
        # return if no comparison needed
        if len(selected) < 2:
            return
        labelx = []
        labely = []
        for index in selected:
            x = index.internalPointer()
            if len(x.values) > 0:
                labelx.append(x.values[0].label[0])
                labely.append(x.values[0].label[1])

        if all(x == labelx[0] for x in labelx) and all(x == labely[0] for x in labely):
            return

        else:
            QtWidgets.QMessageBox.information(self, "Error!",
                                              "You should not choose curves with different units.")
            selectionmodel.clearSelection()

    # updates the plot if the plot variable is changed
    def update_plot(self):
        # user-generated curves and curves loaded from files are not supposed to be mixed
        user_generated_curves = False
        if self.sender() == self._variable_tree_selection_model or self.sender() == self.curveListSelectionModel:
            self.check_labels()
            data_collection = self.get_plot_data_collection_from_selected_variables()
            data_collection_user_generated = []
            for index in self.curveListView.selectedIndexes():
                data_collection_user_generated.append(self.curveListModel[index.data()])
        else:
            return

        plot_data_collection = data_collection + data_collection_user_generated
        if len(data_collection_user_generated):
            self.plotPreview.tableView.setModel(self.bdUserGeneratedTableModel)
            self.plotPreview.change_plot(plot_data_collection, True)
        else:
            self.plotPreview.tableView.setModel(self.bdTableModel)
            self.update_table(data_collection)
            self.plotPreview.change_plot(plot_data_collection, False)
        if len(data_collection) and len(data_collection_user_generated):
            # don't mix user-generated and normal curves
            self.plotPreview.tableView.hide()
            self.plotPreview.label_warning.show()
            return

        self.plotPreview.tableView.show()
        self.plotPreview.label_warning.hide()
        self.plotPreview.tableView.model().update(plot_data_collection, self.combo_rate_psnr.currentText(),
                                     self.combo_interp.currentText(), not(self.checkBox_bdplot.isChecked()))

    def get_table_header(self, plot_data_collection):
        tmp_legend = []
        tmp_config = []

        # make legend
        for plot_data in plot_data_collection:
            tmp = []
            for identifiers in plot_data.identifiers[1:]:
                tmp += identifiers.split(sep)
            tmp2 = tmp + plot_data.path
            tmp_legend.append(tmp2)
            tmp_config.append(tmp)

        legend = []
        config = []
        for c in tmp_legend:
            result = list(filter(lambda x: all(x in l for l in tmp_legend) == False, c))
            if result == []: result = [plot_data.path[-1]]
            legend.append(" ".join(result))
        if len(tmp_legend) == 1:
            legend = [plot_data.path[-1]]

        #make config
        for c in tmp_config:
            result = list(filter(lambda x: all(x in l for l in tmp_config) == False, c))
            if ((set([" ".join(result)]) - set(config) != set()) & (result != [])): config.append(" ".join(result))

        result = (legend, config)
        return result

    #updates the table
    def update_table(self,plot_data_collection):

        self.tableWidget.clear()
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)

        if plot_data_collection != []:
            if 'Temporal' in plot_data_collection[0].path: self.change_table_temporal(plot_data_collection)
            else: self.change_table_summary(plot_data_collection)

        self.tableWidget.resizeColumnsToContents()

    def change_table_temporal(self, plot_data_collect):

        plot_data_collection = plot_data_collect
        self.tableWidget.setRowCount(len(plot_data_collection))
        plot_count = data_count = 0
        data_names = []
        plot_data_collection.sort(key=lambda plot_data: (plot_data.identifiers))
        legend = self.get_table_header(plot_data_collection)
        header = legend[0]

        for plot_data in plot_data_collection:
            values = ((float(x), float(y)) for (x, y) in plot_data.values)

            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list(zip(*sorted_value_pairs))

            # make header
            if plot_data.identifiers[0] not in data_names:
                self.tableWidget.insertRow(plot_count)
                v_item = QtWidgets.QTableWidgetItem(str(plot_data.identifiers[0]))
                font = self.tableWidget.font()
                v_item.setData(6, QtGui.QFont(self.tableWidget.font().setBold(True)))
                v_item.setData(6, QtGui.QFont("Ubuntu", 11, QtGui.QFont.Bold))
                self.tableWidget.setVerticalHeaderItem(plot_count, v_item)
                header_count = plot_count
                data_names.append(plot_data.identifiers[0])
                plot_count += 1

            # round data
            if plot_data.label[1] == 'dB':
                ys = tuple(map(lambda i: round(i, 1), ys))

            self.tableWidget.horizontalHeader().setVisible(False)
            # fill up column per column
            for column_count in range(0, len(xs)):

                self.tableWidget.setCurrentCell(plot_count, column_count)
                if column_count > self.tableWidget.currentColumn():   self.tableWidget.insertColumn(column_count)
                self.tableWidget.setItem(plot_count, column_count, QtWidgets.QTableWidgetItem(str(ys[column_count])))
                self.tableWidget.setVerticalHeaderItem(plot_count, QtWidgets.QTableWidgetItem(str(header[data_count])+ " [" + str(plot_data.label[1]) + "] "))
                new_item = QtWidgets.QTableWidgetItem(str(xs[column_count]))
                new_item.setData(6, QtGui.QFont("Ubuntu", 11, QtGui.QFont.Bold))
                self.tableWidget.setItem(header_count, column_count, new_item)

                column_count += 1

            plot_count += 1
            data_count += 1

    def change_table_summary(self, plot_data_collect):

        plot_data_collection = plot_data_collect
        header_count = plot_count = data_count = config_count = column_saver = 0
        data_names = []
        plot_data_collection.sort(key=lambda plot_data: plot_data.path[-1])
        plot_data_collection.sort(key=lambda plot_data: plot_data.identifiers[0])
        legend = self.get_table_header(plot_data_collection)
        header = legend[0]
        config = legend[1]

        if ((config == []) | (len(config) == 1)):
            self.change_table_temporal(plot_data_collection)
            return

        self.tableWidget.setRowCount(len(plot_data_collection)/len(config))

        for plot_data in plot_data_collection:

            values = ((float(x), float(y)) for (x, y) in plot_data.values)

            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list(zip(*sorted_value_pairs))

            # make header, important if more than one plot
            if plot_data.identifiers[0] not in data_names:
                self.tableWidget.insertRow(plot_count)
                v_item = QtWidgets.QTableWidgetItem(str(plot_data.identifiers[0]))
                v_item.setData(6, QtGui.QFont("Ubuntu", 11, QtGui.QFont.Bold))
                self.tableWidget.setVerticalHeaderItem(plot_count, v_item)
                header_count = plot_count
                data_names.append(plot_data.identifiers[0])
                plot_count += 1

            # round data
            if plot_data.label[1] == 'dB':
                ys = tuple(map(lambda i: round(i, 1), ys))

            #horizontal header if more than one config
            if len(config) > 1: self.tableWidget.horizontalHeader().setVisible(True)
            else: self.tableWidget.horizontalHeader().setVisible(False)

            for column_count in range(0, len(xs)):

                columns = column_saver + column_count
                if (((column_saver+column_count) >= self.tableWidget.columnCount()) | (self.tableWidget.columnCount()==0) ):
                    self.tableWidget.insertColumn(column_saver + column_count)
                if plot_count >= self.tableWidget.rowCount():
                    self.tableWidget.insertRow(plot_count)
                # units in first row of table
                new_item = QtWidgets.QTableWidgetItem(plot_data.label[0] + ' | ' + plot_data.label[1])
                new_item.setData(6, QtGui.QFont("Ubuntu", 11, QtGui.QFont.Bold))
                self.tableWidget.setItem(header_count, column_saver + column_count, new_item)
                #self.tableWidget.setItem(header_count, column_saver + column_count, QtWidgets.QTableWidgetItem(plot_data.label[0] + ' | ' + plot_data.label[1]))
                # x and y-value in one cell
                self.tableWidget.setItem(plot_count, columns, QtWidgets.QTableWidgetItem(str(xs[column_count]) + ' | ' + str(ys[column_count])))
                # header
                self.tableWidget.setHorizontalHeaderItem(column_saver+column_count, QtWidgets.QTableWidgetItem(str(config[config_count])))
                column_count += 1

            if config[config_count] == header[data_count]: header[data_count] =  header[data_count].replace(config[config_count], plot_data.path[-1])
            elif config[config_count] in header[data_count]: header[data_count] = header[data_count].replace(config[config_count], '')

            self.tableWidget.setVerticalHeaderItem(plot_count, QtWidgets.QTableWidgetItem(str(header[data_count])))
            column_saver = column_saver + column_count
            config_count += 1

            if config_count == len(config):
                plot_count += 1
                column_saver = config_count = 0
            data_count += 1

    def update_bd_table(self, index):
        # update bd table, the index determines the anchor,
        # if it is non integer per default the first config is regarded as
        # anchor

        self.bdTableModel.update_table(self.combo_rate_psnr.currentText(),
                                           self.combo_interp.currentText(), index,
                                       not(self.checkBox_bdplot.isChecked()))

    def update_bd_user_generated_curves_table(self, index):
        clicked_text = self.bdUserGeneratedTableModel.headerData(index, Qt.Vertical, Qt.DisplayRole)
        self.bdUserGeneratedTableModel.update(None, self.combo_rate_psnr.currentText(),
                                           self.combo_interp.currentText(), not(self.checkBox_bdplot.isChecked()),
                                              clicked_text)

    def update_bd_plot(self):
        data_collection = self.get_plot_data_collection_from_selected_variables()
        data_collection_user_generated = []
        for index in self.curveListSelectionModel.selectedIndexes():
            data_collection_user_generated.append(self.curveListModel[index.data()])

        if len(data_collection):
            self.bdTableModel.update(data_collection, self.combo_rate_psnr.currentText(),
                                 self.combo_interp.currentText(), not (self.checkBox_bdplot.isChecked()))
        elif len(data_collection_user_generated):
            self.bdTableModel.update(data_collection_user_generated, self.combo_rate_psnr.currentText(),
                                     self.combo_interp.currentText(), not (self.checkBox_bdplot.isChecked()))

    def export_table_to_csv(self):
        # remember that the decimal mark is '.'
        if self.tableWidget.rowCount() > 0:
            path, extension = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table View as', '.', 'CSV (*.csv)')
            if path != '':      
                if '.csv' not in path:
                    path += '.csv'  
                with open(str(path), 'w', newline='') as stream:
                    writer = csv.writer(stream)
                    for row in range(self.tableWidget.rowCount()):
                        rowdata = []
                        rowdata.append(str(self.tableWidget.verticalHeaderItem(row).data(0))) #data(0) = data(Qt.displayRole)
                        for column in range(self.tableWidget.columnCount()):
                            item = self.tableWidget.item(row, column)
                            if item is not None:
                                rowdata.append(str(item.text()))
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)

    def save_bd_table(self):
        if self.bdTableModel.rowCount(self) == 0:
            return
        filename, extension = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Table as', '.', 'Latex (*.tex)')
        if filename != '':      
            if '.tex' not in filename:
                filename += '.tex'  
            self.bdTableModel.export_to_latex(filename)

    def on_combo_box(self):
        # just update the bd table but do not change the anchor
        self.update_bd_table(-1)

    def save_current_selection(self):
        """Saves the current selected sim data item collection"""
        if not self.get_selected_simulation_data_items():
            msg = QtWidgets.QMessageBox(self)  # use self as parent here
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("You did not select any simulation data item to store\n"
                        "Please make a selection and try again.")
            msg.setWindowTitle("Info")
            msg.show()
            return        
        filename, extension = QtWidgets.QFileDialog.getSaveFileName(self, 'Save RD data as', '.', 'RDPlot (*.rd)')
        if filename != '':      
            if '.rd' not in filename:
                filename += '.rd'  
            f = open(filename, 'w')
            f.write(jsonpickle.encode(self.get_selected_simulation_data_items()))
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
                self.simDataItemTreeModel.update(sim_data_items,False)
                f.close()
                continue

            self.simDataItemTreeView.msg.show()
            self.simDataItemTreeView.parserThread.add_path(path)
            self.simDataItemTreeView.parserThread.start()

    def open_about_page(self):
        """Opens and displays an Html About file"""
        try:
            html_path = path.abspath(here + '/docs/about.html')
            html_file = open(html_path, 'r', encoding='utf-8', errors='ignore')
            source_code = html_file.read()

            try:
                f = open(here + '/version.txt', 'r')
                app_version = f.readline()
            except:
                app_version = 'could not detect version'

            source_code = source_code.replace("##VERSION##", app_version)
            source_code = source_code.replace("##here##", here)
            about_dialog = QtWidgets.QDialog(self)
            about_dialog.setWindowTitle("About RDPlot")
            about_dialog.setMaximumSize(950, 800)
            about_text = QtWidgets.QTextBrowser(about_dialog)
            about_text.setMinimumWidth(950)
            about_text.setMinimumHeight(800)
            about_text.setHtml(source_code)
            about_text.setOpenExternalLinks(True)
            about_text.show()
            about_dialog.exec_()
            about_dialog.close()
            about_text.close()
        except IOError:
            html_error = QtWidgets.QMessageBox()
            html_error.setIcon(QtWidgets.QMessageBox.Critical)
            html_error.setText("Error opening about or help")
            html_error.setInformativeText("The html file from the resource could not be loaded.")
            html_error.exec_()

    def generate_new_curve(self):
        plot_data_collection = self.get_plot_data_collection_from_selected_variables()
        if plot_data_collection:
            new_plot_values = []
            for _plot_data in plot_data_collection:
                new_plot_values.extend(_plot_data.values)
            if len(new_plot_values) < 4:
                    QtWidgets.QMessageBox.warning(self, "Warning!", "You didn't select at least 4 points.")
            else:
                curve_name, ok = QtWidgets.QInputDialog.getText(self, "New curve", "Please enter a name for the new curve.\n"
                                            "If you enter an already existing name,\nits data will be overwritten.")
                curve_name = curve_name.strip()
                if curve_name is not '':
                    new_plot_data = PlotData([curve_name], new_plot_values, [],
                                             plot_data_collection[0].label)
                    self.add_curve(curve_name, new_plot_data)
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning!", "Please enter a valid name.")
        else:
            QtWidgets.QMessageBox.warning(self, "Warning!", "You didn't select at least 4 points.")

    def add_curve(self, name, data):
        if self.curveWidget.isHidden():
            self.curveWidget.show()
        data_tuple = (name, data)
        self.curveListModel.update_from_tuples((data_tuple,))
        # all_indexes = QItemSelection(self.curveListModel.index(0),
        #                             self.curveListModel.index(self.curveListModel.rowCount(QModelIndex())))
        # self.curveListSelectionModel.select(all_indexes, QItemSelectionModel.Clear)
        # self.curveListSelectionModel.select(self.curveListModel.index(self.curveListModel.rowCount(QModelIndex())-1),
        #                                    QItemSelectionModel.Select)
        # self.curveListView.setFocus()

    def remove_curves(self):
        # todo integrate bjontegaard for generated curves(should be fully functional already)
        curves_to_remove = []
        for index in self.curveListSelectionModel.selectedIndexes():
            curves_to_remove.append(index.data())
        self.curveListModel.remove_keys(curves_to_remove)
        if len(self.curveListModel) > 0:
            self.curveListSelectionModel.select(self.curveListModel.index(0), QItemSelectionModel.Select)
        else:
            self.curveWidget.hide()
            self.update_plot()

    def get_recent_files(self):
        recent_files = self.settings.value('recentFiles')
        if recent_files is not None:
            for recent_file in recent_files:
                if path.exists(recent_file):
                    action = self.menuRecent_files.addAction(recent_file)
                    action.triggered.connect(self.open_recent_file)

    def open_recent_file(self):
        path_recent = self.sender().text()
        if path.isdir(path_recent):
            self.simDataItemTreeView.add_folder(path_recent)
        else:
            self.simDataItemTreeView.add_file(path_recent)

    def add_recent_files(self, files, reload):
        # files doesn't necessarily have to just be a list of files
        # it can also be a directory
        if not reload:
            recent_files = self.settings.value('recentFiles')
            if recent_files is None:
                recent_files = []
            for file in files:

                if file in recent_files:
                    # put our file on top of the list
                    recent_files.remove(file)
                recent_files.insert(0, file)
            while len(recent_files) > 5:
                del recent_files[-1]
            self.settings.setValue('recentFiles', recent_files)

            self.menuRecent_files.clear()
            for recent_file in recent_files:
                if path.exists(recent_file):
                    action = self.menuRecent_files.addAction(recent_file)
                    action.triggered.connect(self.open_recent_file)

    def add_files_to_watcher(self, items):
        for item in items:
                if isfile(item.path):
                    self.watcher.addPath(item.path)

    def warning_file_change(self, path_item):
        # inform user about the fact that one of the loaded files has been changed since the application has started
        # timer is used to avoid spamming the user when multiple files are deleted in a row
        # retrieve affected notes and parent nodes
        # change their style in the tree view to indicate which files are affected
        if self.show_file_changed_message:
            self.show_file_changed_message = False
            self.reset_timer.start()
            QtWidgets.QMessageBox.warning(self, 'File change', 'One or more of your loaded files have been changed.\n'
                                                               'You can choose to reload them.\n'
                                                               'Hint: Changed files are greyed out in the sequences widget.')
        else:
            self.reset_timer.stop()
            self.reset_timer.start()

        affected_notes = []
        for leaf in self.simDataItemTreeModel.root.leafs:
            for value in leaf.values:
                if value.path == path_item:
                    affected_notes.append(leaf)
        for node in affected_notes:
            node_index = self.simDataItemTreeModel._get_index_from_item(node)
            node.setProperty('needs_reload', 'True')
            parent = self.simDataItemTreeModel.parent(node_index)
            level = 0
            while parent.isValid() and level < 2: #MAX_LEVEL
                parent.internalPointer().setProperty('needs_reload', 'True')
                parent = self.simDataItemTreeModel.parent(parent)
                level += 1

    def _reset_file_changed_message(self):
        self.show_file_changed_message = True

    def reload_files(self):
        # remove all selected files first
        # reload available files
        # could possibly limit this to only files that we know have been changed
        def check_children(parent):
            if len(parent.children) > 0:
                for child in parent.children:
                    if not check_children(child):
                        return False
                parent.setProperty('needs_reload', 'False')
                return True
            else:
                if parent.property('needs_reload') == 'True':
                    return False
                return True

        values = self.selectedSimulationDataItemListModel.values()
        if len(values) == 0:
            for index in self.simDataItemTreeModel.root.leafs:
                for sim_data_item in index.values:
                    values.append(sim_data_item)
        items_to_be_reloaded = []
        for value in values:
            if path.exists(value.path):
                # reload file
                items_to_be_reloaded.append(value)

        self._variable_tree_selection_model.selectionChanged.disconnect()
        self._selection_model.selectionChanged.disconnect(self.change_list)
        self.simDataItemTreeModel.remove(values)

        self.simDataItemTreeView.msg.show()
        for item in items_to_be_reloaded:
            self.simDataItemTreeView.add_file(item.path, reload=True)

        self.change_list(QItemSelection(), QItemSelection())
        self._selection_model.selectionChanged.connect(self.change_list)
        self._variable_tree_selection_model.selectionChanged.connect(self.update_plot)

        for node in self.simDataItemTreeModel.root.children:
            # remove grey font color if all changed files have been reloaded
            # have to check every single item because possible deletion of older nodes makes things very difficult
            check_children(node)

    def show_sequences_context_menu(self, position):
        self.menuEdit.exec(self.simDataItemTreeView.mapToGlobal(position))

    # def bd_user_generated_curves(self):
    #    pass
