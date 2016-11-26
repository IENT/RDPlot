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
        self.sequences = {}

        # set up signals and slots
        # self.sequenceListWidget.itemClicked.connect(self.plotPreview.change_plot)
        self.sequenceListWidget.currentItemChanged.connect(self.update_plot)
        self.addSequenceButton.clicked.connect(self.add_sequence)
        self.addPlotButton.clicked.connect(self.addAnotherPlot)
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

        # extract the part of the filename that files for different QPs share.
        sequence_name_common = file_name.rsplit('_QP', 1)[0]
        sequence_files = glob(directory + '/' + sequence_name_common + '*')
        sequence = Sequence(sequence_name_common, sequence_files)

        self.sequences[sequence.name] = sequence
        self.sequenceListWidget.addItem(sequence.name)
        self.sequenceListWidget.setCurrentItem(self.sequenceListWidget.item(self.sequenceListWidget.count()-1))

        pass

    def update_plot(self, item):
        # updates the plot with a new figure.
        sequence_name = item.text()
        sequence = self.sequences[sequence_name]

        # get currently chosen plot variable
        former_variable = self.comboBox.currentText()

        # update available variables available for this sequence
        # determine the plottype
        # add found plot variables to combo box
        all_variable_names = set()  # set because we don't want duplicates
        if self.summaryPlotButton.isChecked():
            plot_data = sequence.summary_data.items()
        else:
            plot_data = sequence.temporal_data.items()

        for (summary, variable_dicts) in plot_data:
            # all_variable_names.add(variable_dicts.keys())
            for variable_name in variable_dicts.keys():
                all_variable_names.add(variable_name)
        self.comboBox.clear()
        self.comboBox.addItems(all_variable_names)

        # use same variable as with last plot if possible
        new_variable = ''
        if former_variable in all_variable_names:       # todo: set some smarter defaults here? Problem is the recursive calling
            new_variable = former_variable
            #self.comboBox.setCurrentText(new_variable)
        else:
            if 'YUV-PSNR' in all_variable_names:
                #new_variable = 'YUV-PSNR'
                #self.comboBox.setCurrentText(new_variable)
                pass
            elif 'Y-PSNR' in all_variable_names:
                #new_variable = 'Y-PSNR'
                #self.comboBox.setCurrentText(new_variable)
                pass
            else:
                #self.comboBox.setCurrentIndex(0)
                pass

        #self.plotPreview.change_plot(sequence, new_variable, self.summaryPlotButton.isChecked())

    def update_plot_type(self, checked):
        currentItem = self.sequenceListWidget.currentItem()
        if currentItem is None:
            return
        self.update_plot(self.sequenceListWidget.currentItem())

    def update_plot_variable(self, index):
        index_name = self.comboBox.itemText(index)
        if not index_name:
            return
        # self.plotPreview.change_YUVMod(index_name)
        sequence_item = self.sequenceListWidget.currentItem()
        if sequence_item is not None:
            sequence_name = sequence_item.text()
            sequence = self.sequences[sequence_name]
            self.plotPreview.change_plot(sequence, index_name, self.summaryPlotButton.isChecked())



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

    def change_plot(self, sequence, variable, plotTypeSummary):
        qp_vals = [int(qp) for qp in sequence.qp_vals]
        if not variable:
            return

        if plotTypeSummary:
            # np
            rate = sequence.summary_data['SUMMARY']['Bitrate']
            plot_variable = sequence.summary_data['SUMMARY'][variable]

            fig = Figure()
            axis = fig.add_subplot(111)
            axis.plot(rate, plot_variable)
        else:
            fig = Figure()
            axis = fig.add_subplot(111)
            for i in range(0, len(qp_vals)):
                #framevalues = sequence.temporal_data[qp_vals[i]]['Frame']
                axis.plot(sequence.temporal_data[str(qp_vals[i])]['Frame'],
                          sequence.temporal_data[str(qp_vals[i])][variable])

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


class Sequence():
    """"Keeps all information on a sequence.
    The appropriate encoder logs are processed once, extracting all relevant information.
    Offers methods for extracting the information from the logs.
    """

    def __init__(self, sequence_name_common, sequence_files):
        self.log_files = {}
        self.name = ""
        self.qp_vals = []
        self.sequence_files = {}  # will fill this with the list sequence_files with qp as key after they are extracted
        self.summary_data = {}
        self.temporal_data = {}

        self.name = sequence_name_common
        self.extract_qp_vals(sequence_files)
        self.extract_rd_vals()
        self.extract_temporal_vals()

    def extract_qp_vals(self, sequence_files):
        for sequence_file in sequence_files:
            m = re.search(r'_QP(\d*)_', sequence_file)
            if m:
                qp_val = m.group(1)
                self.qp_vals.append(qp_val)
                self.sequence_files[qp_val] = sequence_file
            else:
                print('No match for QP value in sequence name')  # todo: notify user, exception?
        self.qp_vals.sort(reverse=True)

    def extract_temporal_vals(self):
        #this function extracts temporal values
        for qp in self.qp_vals:
            file = self.sequence_files[qp]
        # for (qp, file) in self.sequence_files.items():
            with open(file, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries_qp = re.findall(r"""
                    POC \s+ (\d+) \s+ .+ \s+ \d+ \s+ . \s+ (.-\D+) ,  #Slice
                    \s .+ \) \s+ (\d+) \s+ (.+) \s+ \[ (\D+) \s+ (\d+.\d+) \s+ #Y PSNR
                    \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # U PSNR
                    \D+ \s+ (\D+) \s+ (\d+.\d+) \s+ # v PSNR
                    """, log_text, re.M + re.X)
                frames = []
                yPsnr = []
                uPsnr = []
                vPsnr = []
                #slice = []
                rate = []
                for i in range(0, len(summaries_qp)):
                    frames.append(summaries_qp[i][0])
                    #slice.append(summaries_qp[i][1])
                    rate.append(summaries_qp[i][2])
                    yPsnr.append(summaries_qp[i][5])
                    uPsnr.append(summaries_qp[i][7])
                    vPsnr.append(summaries_qp[i][9])
                tempdata = {'Frame': frames, 'Bits': rate,
                        'Y-PSNR': yPsnr, 'U-PSNR': uPsnr, 'V-PSNR': vPsnr}
                self.temporal_data[qp] = tempdata

    def extract_rd_vals(self):
        """
        This functions find all data matching the Regex format specified below and stores it in dicts in the sequence.
        Care was taken to avoid coding explicit names, like 'Y-PSNR', 'YUV-PSNR', etc...
        """
        for qp in self.qp_vals:
            file = self.sequence_files[qp]
        # for (qp, file) in self.sequence_files.items():
            with open(file, 'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                summaries_qp = re.findall(r"""  ^(\w*)-*.*$ # catch summary line
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)# catch rest of the line
                               \s* # catch newline and space
                               (\d*\s*)\w # catch frame number
                               (\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*) # catch the fractional number (rate, PSNRs)
                          """, log_text, re.M + re.X)

                for summary in summaries_qp:
                    summary_type = summary[0]
                    if summary_type not in self.summary_data:  # create upon first access
                        self.summary_data[summary_type] = {}
                    names = summary[1:7]
                    vals = summary[7:]

                    names = [name.strip() for name in names]  # remove leading and trailing space
                    vals = [float(val) for val in vals]  # convert to numbers

                    name_val_dict = dict(zip(names, vals))  # pack both together in a dict
                    # print(summary_type)

                    # now pack everything together
                    for name in names:
                        if name not in self.summary_data[summary_type]: # create upon first access
                            self.summary_data[summary_type][name] = []
                        self.summary_data[summary_type][name].append(name_val_dict[name])


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
