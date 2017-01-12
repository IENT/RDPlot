from PyQt5.uic import loadUiType
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt4agg import (
#     FigureCanvasQTAgg as FigureCanvas,
#     NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from glob import glob
import re
import collections
import numpy as np

from model import (EncLog, EncoderLogTreeModel, summary_data_from_enc_logs,
                   sort_dict_of_lists_by_key, OrderedDictModel)
from view import (EncLogTreeView, QRecursiveSelectionModel)


Ui_MainWindow, QMainWindow = loadUiType('mainWindow.ui')
Ui_PlotWidget, QWidget = loadUiType('plotWidget.ui')


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

        # Create tree model to store encoder logs and connect it to view
        self.encoderLogTreeModel = EncoderLogTreeModel()
        self.encoderLogTreeView.setModel(self.encoderLogTreeModel)

        # Set custom selection model, so that sub items are automatically
        # selected if parent is selected
        self._selection_model = QRecursiveSelectionModel(self.encoderLogTreeView.model())
        self.encoderLogTreeView.setSelectionModel(self._selection_model)

        # Connect list view with model for the selected values of tree view
        self.selectedEncoderLogListModel = OrderedDictModel()
        self.encoderLogListView.setModel( self.selectedEncoderLogListModel )
        self._selection_model.selectionChanged.connect(self.change_list)

        # set up signals and slots
        self.selectedEncoderLogListModel.rowsInserted.connect(self.update_plot)
        self.selectedEncoderLogListModel.rowsRemoved.connect(self.update_plot)

        # Connect signals of menues
        self.actionOpen_File.triggered.connect(
            self.encoderLogTreeView.add_encoder_log
        )
        self.actionOpen_Sequence.triggered.connect(
            self.encoderLogTreeView.add_sequence
        )
        self.actionOpen_Directory.triggered.connect(
            self.encoderLogTreeView.add_folder
        )

        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)
        self.summaryPlotButton.toggled.connect(self.update_plot_type)

        self.encoderLogTreeView.deleteKey.connect(self.remove)

    def remove(self):
        for value in self.selectedEncoderLogListModel.values():
            if value in self.selectedEncoderLogListModel.values():
                self.encoderLogTreeModel.remove(value)

    def change_list(self, q_selected, q_deselected):
        """Extend superclass behavior by automatically adding the values of
           all selected items in :param: `q_selected` to value list model. """

        for q_index in q_selected.indexes():
            # Add values, ie. data stored at the item, to the list model
            for value in q_index.internalPointer().values:
                    self.selectedEncoderLogListModel[str(value)] = value

        for q_index in q_deselected.indexes():
            # Remove values, ie. data stored at the item, from the list model
            for value in q_index.internalPointer().values:
                key =  str(value)
                # TODO Why is this check necesarry? Asynchron access?
                if key in self.selectedEncoderLogListModel:
                    self.selectedEncoderLogListModel.pop( key )
    def get_selected_enc_logs(self):
        return [self.selectedEncoderLogListModel[key] for key in self.selectedEncoderLogListModel]

    def update_plot(self):
        # updates the plot with a new figure.
        # self.selectedEncoderLogListModel.dataChanged.connect(self.update_plot)

        encLogs = self.get_selected_enc_logs()

        # get currently chosen plot variable
        former_variable = self.comboBox.currentText()

        # update available variables available for this sequence
        # determine the plottype
        # add found plot variables to combo box
        all_variable_names = []  # set because we don't want duplicates
        if self.summaryPlotButton.isChecked():
                plot_data = summary_data_from_enc_logs(encLogs)
        else:
            plot_data = {encLog.sequence + ' ' + encLog.config : encLog.temporal_data for encLog in encLogs}

        for seqconf in plot_data:
            for a in plot_data[seqconf]:
                for variable_name in plot_data[seqconf][a].keys():
                    all_variable_names.append(variable_name)
                break
            break

        all_variable_names.sort()
        self.comboBox.currentIndexChanged.disconnect(self.update_plot_variable)
        self.comboBox.clear()
        self.comboBox.addItems(all_variable_names)
        # use same variable as with last plot if possible
        skip = False
        if former_variable in all_variable_names:       # todo: set some smarter defaults here? Problem is the recursive calling
            new_variable = former_variable
            self.comboBox.setCurrentText(new_variable)
        else:
            if 'YUV-PSNR' in all_variable_names:
                new_variable = 'YUV-PSNR'
                self.comboBox.setCurrentText(new_variable)
                pass
            elif 'Y-PSNR' in all_variable_names:
                new_variable = 'Y-PSNR'
                self.comboBox.setCurrentText(new_variable)
                pass
            else:
                self.comboBox.setCurrentIndex(0)
                skip = True
        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)
        # self.selectedEncoderLogListModel.dataChanged.connect(self.update_plot)

        # TODO implement handling of no correctly parsed data
        if skip == False:
            self.plotPreview.change_plot(encLogs, new_variable, self.summaryPlotButton.isChecked())

    # updates the plot if the type is changed
    def update_plot_type(self, checked):
        self.encoderLogTreeModel.is_summary_enabled = checked

        # TODO enable if selection is implemented
        # if len(self.encoderLogTreeView.selectedItems()) == 0:
        #     return
        # self.update_plot()

    # updates the plot if the plot variable is changed
    def update_plot_variable(self, index):
        self.comboBox.currentIndexChanged.disconnect(self.update_plot_variable)
        index_name = self.comboBox.itemText(index)
        if not index_name:
            return
        if len( self.encoderLogTreeView.selectedItems() ) != 0:
            self.plotPreview.change_plot(
                self.get_selected_enc_logs(),
                index_name,
                self.summaryPlotButton.isChecked(),
            )
        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)

class NestedDict(dict):
    """
    Provides the nested dict used to store all the sequence data.
    """

    def __getitem__(self, key):
        if key in self: return self.get(key)
        return self.setdefault(key, NestedDict())


class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, ):
        super(PlotWidget, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        fig = Figure()
        self.addmpl(fig)

    # refreshes the figure according to new changes done
    def change_plot(self, encLogs, variable, plotTypeSummary):
        if not variable:
            return

        # put a subplot into the figure and set the margins a little bit tighter than the defaults
        # this is some workaround for PyQt similar to tight layout
        fig = Figure()
        axis = fig.add_subplot(111)
        fig.subplots_adjust(left=0.05, right=0.95,
                                    bottom=0.1, top=0.95,
                                    hspace=0.2, wspace=0.2)

        # distinguish between summary plot and temporal plot
        if plotTypeSummary:
            summary_data = summary_data_from_enc_logs(encLogs)
            for seqconf in summary_data:
                summary = summary_data[seqconf]['SUMMARY']
                summary = sort_dict_of_lists_by_key(summary, 'Bitrate')
                rate          = summary['Bitrate']
                plot_variable = summary[variable]

                axis.plot(rate, plot_variable,'x-')
                axis.set_title('Summary Data')
                axis.set_xlabel('Bitrate [kbps]') #TODO is that k bytes or bits? need to check
                axis.set_ylabel(variable + ' [dB]')
        else:
            for encLog in encLogs:
                #TODO frames are not consecutive eg. [8, 4, 2, 6, 10, 4, ...] in HEVC
                #TODO multiple subplots for different QPS
                frames = encLog.temporal_data[encLog.qp]['Frames']
                values = encLog.temporal_data[encLog.qp][variable]
                axis.plot(values)
                axis.set_title('Temporal Data')
                axis.set_xlabel('POC')
                axis.set_ylabel(variable + ' [dB]')

        self.updatempl(fig)

    # TODO Remove this? It will not work with the tree widget
    # def addfig(self, name, fig):
    #     self.fig_dict[name] = fig
    #     self.encoderLogTreeView.addItem(name)

    # updates the figure with a new figure
    def updatempl(self, fig):
        self.rmmpl()
        self.addmpl(fig)
        pass

    # adds a figure to the plotwidget
    def addmpl(self, fig):
        # set backgroung to transparent
        fig.patch.set_alpha(0)
        # set some properties for canvas and add it to the vertical layout.
        # Most important is to turn the vertical stretch on as otherwise the plot is only scaled in x direction when rescaling the window
        self.canvas = FigureCanvas(fig)
        self.canvas.setParent(self.plotAreaWidget)
        policy = self.canvas.sizePolicy()
        policy.setVerticalStretch(1)
        self.canvas.setSizePolicy(policy)
        self.verticalLayout.addWidget(self.canvas)
        # add the toolbar for the plot
        self.toolbar = NavigationToolbar(self.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.verticalLayout.addWidget(self.toolbar)
        pass

    # removes a figure from the plotwidget
    def rmmpl(self, ):
        self.verticalLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.verticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()


class Graph():
    """"
    Hold all information on a single plot of a sequence.
    """

    def __init__(self):
        self.rd_points = {}


if __name__ == '__main__':
    import sys
    from PyQt5 import QtGui
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
