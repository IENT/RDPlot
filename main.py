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
from os.path import join

from model import (EncLog, EncLogCollection, summary_data_from_enc_logs,
                   sort_dict_of_lists_by_key)


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

        # store the sequences
        self.encLogCollection = EncLogCollection()

        # set up signals and slots
        self.sequenceListWidget.currentItemChanged.connect(self.update_plot)
        self.addSequenceButton.clicked.connect(self.add_sequence)
        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)
        self.summaryPlotButton.toggled.connect(self.update_plot_type)

    def add_sequence(self):  # todo: put his logic in its own widget and class, should belong to a listSequencesWidget
        # extract folder and filename
        self.addSequenceButton.clicked.disconnect(self.add_sequence)
        while 1:
            try:
                self.filename = QtWidgets.QFileDialog.getOpenFileNames(
                    self,
                    "Open Sequence Encoder Log",
                    "/home/ient/Software/rd-plot-gui/examplLogs",
                    "Enocder Logs (*.log)")
                [directory, file_name] = self.filename[0][0].rsplit('/', 1)
            except IndexError:
                return
            else:
                print("successfully added sequence")
                break

        path = join(directory, file_name)
        encLogs = list( EncLog.parse_directory_for_sequence( path ) )
        self.encLogCollection.update(encLogs)
        
        self.sequenceListWidget.addItem(encLogs[0].sequence)
        # TODO implement reloading
        self.sequenceListWidget.setCurrentItem(self.sequenceListWidget.item(self.sequenceListWidget.count()-1))

        self.addSequenceButton.clicked.connect(self.add_sequence)
        pass

    def update_plot(self, item):
        # updates the plot with a new figure.
        sequence_name = item.text()
        #TODO correct access
        encLogs = self.encLogCollection.get_by_sequence(sequence_name)

        # get currently chosen plot variable
        former_variable = self.comboBox.currentText()

        # update available variables available for this sequence
        # determine the plottype
        # add found plot variables to combo box
        all_variable_names = []  # set because we don't want duplicates
        if self.summaryPlotButton.isChecked():
            plot_data = summary_data_from_enc_logs(encLogs)
        else:
            plot_data = list(encLogs)[0].temporal_data

        for a in plot_data:
            for variable_name in plot_data[a].keys():
                all_variable_names.append(variable_name)
            break
        all_variable_names.sort()
        self.comboBox.currentIndexChanged.disconnect(self.update_plot_variable)
        self.comboBox.clear()
        self.comboBox.addItems(all_variable_names)
        # use same variable as with last plot if possible
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
                pass
        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)
        self.plotPreview.change_plot(self.encLogCollection.get_by_sequence(sequence_name), new_variable, self.summaryPlotButton.isChecked())

    # updates the plot if the type is changed
    def update_plot_type(self, checked):
        currentItem = self.sequenceListWidget.currentItem()
        if currentItem is None:
            return
        self.update_plot(self.sequenceListWidget.currentItem())

    # updates the plot if the plot variable is changed
    def update_plot_variable(self, index):
        self.comboBox.currentIndexChanged.disconnect(self.update_plot_variable)
        index_name = self.comboBox.itemText(index)
        if not index_name:
            return
        sequence_item = self.sequenceListWidget.currentItem()
        if sequence_item is not None:
            sequence_name = sequence_item.text()
            self.plotPreview.change_plot(self.encLogCollection.get_by_sequence(sequence_name), index_name, self.summaryPlotButton.isChecked())
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
        if plotTypeSummary:
            # np
            summary_data = summary_data_from_enc_logs(encLogs)['SUMMARY']
            summary_data = sort_dict_of_lists_by_key(summary_data, 'Bitrate')
            rate          = summary_data['Bitrate']
            plot_variable = summary_data[variable]

            fig = Figure()
            axis = fig.add_subplot(111)
            axis.plot(rate, plot_variable)
            axis.set_title('Summary Data')
            axis.set_xlabel('Bitrate')
            axis.set_ylabel(variable)
        else:
            fig = Figure()
            axis = fig.add_subplot(111)
            for encLog in encLogs:
                #TODO frames are not consecutive eg. [8, 4, 2, 6, 10, 4, ...] in HEVC
                frames = encLog.temporal_data[encLog.qp]['Frames']
                values = encLog.temporal_data[encLog.qp][variable]
                axis.plot(values)
                axis.set_title('Temporal Data')
                axis.set_xlabel('Bitrate')
                axis.set_ylabel(variable)

        self.updatempl(fig)

    # adds a sequence to the list/ tree list
    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    # updates the figure with a new figure
    def updatempl(self, fig):
        self.rmmpl()
        self.addmpl(fig)
        pass

    # adds a figure to the plotwidget
    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.verticalLayout.addWidget(self.canvas)
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
