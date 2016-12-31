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

from model import (EncLog, EncLogCollectionModel, summary_data_from_enc_logs,
                   sort_dict_of_lists_by_key)
from model_view import (DictTreeView, get_child_items_from_item,
                        get_top_level_items_from_tree_widget, EncLogTreeView)


Ui_MainWindow, QMainWindow = loadUiType('mainWindow.ui')
Ui_PlotWidget, QWidget = loadUiType('plotWidget.ui')


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        # fig = Figure()
        # self.addmpl(fig)

        self.plotAreaVerticalLayout = QtWidgets.QVBoxLayout()
        self.plotsFrame.setLayout(self.plotAreaVerticalLayout)

        # add a widget for previewing plots, they can then be added to the actual plot
        self.plotPreview = PlotWidget()
        self.plotAreaVerticalLayout.addWidget(self.plotPreview)
        # container for all plots
        # self.plotWidgets = []
        # newPlot = PlotWidget()
        # self.plotWidgets.append(newPlot)
        # self.plotAreaVerticalLayout.addWidget(newPlot)

        # store the sequences
        self.encLogCollectionModel = EncLogCollectionModel()
        self.tree_view = EncLogTreeView(
            self.sequenceTreeWidget,
            model = self.encLogCollectionModel,
            is_qp_expansion_enabled = False,
        )

        self.encLogCollectionModel.update(
            EncLog.parse_directory('../simulation_examples/HEVC/')
        )
        self.encLogCollectionModel.update(
            EncLog.parse_directory('../simulation_examples_back/hm360Lib/')
        )

        # set up signals and slots
        # self.sequenceListWidget.itemClicked.connect(self.plotPreview.change_plot)
        self.sequenceTreeWidget.itemSelectionChanged.connect(self.update_plot)

        self.addSequenceButton.clicked.connect(self.add_sequence)
        # self.addPlotButton.clicked.connect(self.addAnotherPlot)
        self.comboBox.currentIndexChanged.connect(self.update_plot_variable)
        self.summaryPlotButton.toggled.connect(self.update_plot_type)

    def addAnotherPlot(self):
        newPlot = PlotWidget()
        self.plotWidgets.append(newPlot)
        self.plotAreaVerticalLayout.addWidget(newPlot)

    # def preview_plot(self, item):
    #     text = item.text()
    #     self.rmmpl()
    #     self.addmpl(self.fig_dict[text])

    # def addfig(self, name, fig):
    #     self.fig_dict[name] = fig
    #     self.sequenceListWidget.addItem(name)

    #def add_sequences_in_directory(self):

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
        self.encLogCollectionModel.update(encLogs)

        # for enc_log in encLogs:
        #     self.add_enc_log(enc_log)
        # self.sequenceTreeWidget.setCurrentItem(self.sequenceTreeWidget.item(self.sequenceTreeWidget.count()-1))

        self.addSequenceButton.clicked.connect(self.add_sequence)
        pass

    def update_plot(self):
        # updates the plot with a new figure.
        self.sequenceTreeWidget.itemSelectionChanged.disconnect(self.update_plot)

        encLogs = []
        for (sequence, config, qp) in self.tree_view.get_selected_enc_log_keys():
            encLogs.append(self.encLogCollectionModel.get_by_tree_keys(sequence, config, qp))

        # get currently chosen plot variable
        former_variable = self.comboBox.currentText()

        # update available variables available for this sequence
        # determine the plottype
        # add found plot variables to combo box
        all_variable_names = []  # set because we don't want duplicates
        if self.summaryPlotButton.isChecked():
            plot_data = summary_data_from_enc_logs(encLogs)
        else:
            #TODO Combine data
            plot_data = list(encLogs)[0].temporal_data

        for seqconf in plot_data:
            for a in plot_data[seqconf]:
                # all_variable_names.add(variable_dicts.keys())
                for variable_name in plot_data[seqconf][a].keys():
                    all_variable_names.append(variable_name)
                break
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
        # self.sequenceListWidget.currentItemChanged.connect(self.update_plot)
        self.sequenceTreeWidget.itemSelectionChanged.connect(self.update_plot)

        self.plotPreview.change_plot(encLogs, new_variable, self.summaryPlotButton.isChecked())

    def update_plot_type(self, checked):
        self.summaryPlotButton.toggled.disconnect(self.update_plot_type)

        self.tree_view.is_qp_expansion_enabled = checked

        self.summaryPlotButton.toggled.connect(self.update_plot_type)
        if len(self.sequenceTreeWidget.selectedItems()) == 0:
            return
        self.update_plot()

    def update_plot_variable(self, index):
        self.comboBox.currentIndexChanged.disconnect(self.update_plot_variable)
        index_name = self.comboBox.itemText(index)
        if not index_name:
            return
        # self.plotPreview.change_YUVMod(index_name)
        sequence_item = self.sequenceListWidget.currentItem()
        if sequence_item is not None:
            sequence_name = sequence_item.text()
            self.plotPreview.change_plot(self.encLogCollectionModel.get_by_sequence(sequence_name), index_name, self.summaryPlotButton.isChecked())
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
        # self.sequenceListWidget.itemClicked.connect(self.change_plot)
        # self.addSequenceButton.clicked.connect(self.add_sequence)

        fig = Figure()
        self.addmpl(fig)
        # self.YUVMod = 'YUV-PSNR'

    # def change_YUVMod(self, mod):
    #     self.YUVMod = mod

    def change_plot(self, encLogs, variable, plotTypeSummary):
        if not variable:
            return
        if plotTypeSummary:
            # np
            fig = Figure()
            axis = fig.add_subplot(111)

            summary_data = summary_data_from_enc_logs(encLogs)
            for seqconf in summary_data:
                summary = summary_data[seqconf]['SUMMARY']
                summary = sort_dict_of_lists_by_key(summary, 'Bitrate')
                rate          = summary['Bitrate']
                plot_variable = summary[variable]

                axis.plot(rate, plot_variable)
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
                # axis.set_title('Temporal Data')
                axis.set_xlabel('Bitrate')
                axis.set_ylabel(variable)

        self.updatempl(fig)

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    def updatempl(self, fig):
        self.verticalLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.verticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()
        self.canvas = FigureCanvas(fig)
        self.verticalLayout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.verticalLayout.addWidget(self.toolbar)
        # canvas = FigureCanvas(fig)
        # self.verticalLayout.replaceWidget(self.canvas, canvas)
        pass


    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.verticalLayout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.verticalLayout.addWidget(self.toolbar)
        pass

    # This is the alternate toolbar placement. Susbstitute the three lines above
    # for these lines to see the different look.
    #        self.toolbar = NavigationToolbar(self.canvas,
    #                self, coordinates=True)
    #        self.addToolBar(self.toolbar)

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

    # fig1 = Figure()
    # ax1f1 = fig1.add_subplot(111)
    # ax1f1.plot(np.random.rand(5))
    #
    # fig2 = Figure()
    # ax1f2 = fig2.add_subplot(121)
    # ax1f2.plot(np.random.rand(5))
    # ax2f2 = fig2.add_subplot(122)
    # ax2f2.plot(np.random.rand(10))
    #
    # fig3 = Figure()
    # ax1f3 = fig3.add_subplot(111)
    # ax1f3.pcolormesh(np.random.rand(20,20))

    # app = QtGui.QApplication(sys.argv)
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    # main.addfig('One plot', fig1)
    # main.addfig('Two plots', fig2)
    # main.addfig('Pcolormesh', fig3)
    main.show()
    sys.exit(app.exec_())
