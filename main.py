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
        self.sequenceListWidget.currentItemChanged.connect(self.update_preview)
        self.addSequenceButton.clicked.connect(self.add_sequence)
        self.addPlotButton.clicked.connect(self.addAnotherPlot)

    def addAnotherPlot(self):
        newPlot = PlotWidget()
        self.plotWidgets.append(newPlot)
        self.plotAreaVerticalLayout.addWidget(newPlot)

    def preview_plot(self, item):
        text = item.text()
        self.rmmpl()
        self.addmpl(self.fig_dict[text])

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    def add_sequence(self):  # todo: put his logic in its own widget and class, should belong to a listSequencesWidget
        self.filename = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open Sequence Encoder Log",
            "/home/ient/Software/rd-plot-gui/examplLogs",
            "Enocder Logs (*.log)")

        # extract folder and filename
        [directory, file_name] = self.filename[0][0].rsplit('/', 1)
        # extract the part of the filename that files for different QPs share.
        sequence_name_common = file_name.rsplit('_QP', 1)[0]
        sequence_files = glob(directory + '/' + sequence_name_common + '*')
        sequence = Sequence(sequence_name_common, sequence_files)

        self.sequences[sequence.name] = sequence
        self.sequenceListWidget.addItem(sequence.name)
        debug = self.sequenceListWidget.count()
        self.sequenceListWidget.setCurrentItem(self.sequenceListWidget.item(self.sequenceListWidget.count()-1))

        pass

    def update_preview(self, item):
        sequence_name = item.text()
        sequence = self.sequences[sequence_name]
        self.plotPreview.change_plot(sequence)


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

    def change_plot(self, sequence):
        qp_vals = [int(qp) for qp in sequence.qp_vals]
        qp_vals.sort()
        qp_vals.reverse()
        # np
        rate = []
        psnr = []
        psnrrate = []
        for qp in sequence.qp_vals:
            rate.append(sequence.summary_data['SUMMARY']['Bitrate'][str(qp)])
            psnr.append(sequence.summary_data['SUMMARY']['YUV-PSNR'][str(qp)])

        fig = Figure()
        axis = fig.add_subplot(111)
        axis.plot(rate, psnr)

        self.addmpl(fig)

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.verticalLayout.addWidget(self.canvas)
        self.canvas.draw()
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
        self.summary_data = NestedDict()

        self.name = sequence_name_common
        self.extract_qp_vals(sequence_files)
        self.extract_rd_vals()

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

    def extract_rd_vals(self):
        """
        This functions find all data matching the Regex format specified below and stores it in dicts in the sequence.
        Care was taken to avoid coding explicit names, like 'Y-PSRN', 'YUV-PSNR', etc...
        """
        for (qp, file) in self.sequence_files.items():
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
                    names = summary[1:7]
                    vals = summary[7:]

                    names = [name.strip() for name in names]  # remove leading and trailing space
                    vals = [float(val) for val in vals]  # convert to numbers

                    name_val_dict = dict(zip(names, vals))  # pack both together in a dict
                    # print(summary_type)

                    # now pack everything together
                    for name in names:
                        self.summary_data[summary_type][name][qp] = name_val_dict[name]


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
