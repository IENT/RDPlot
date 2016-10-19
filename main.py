from PyQt4.uic import loadUiType

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from glob import  glob
import  re

Ui_MainWindow, QMainWindow = loadUiType('mainWindow.ui')
Ui_PlotWidget, QWidget = loadUiType('plotWidget.ui')
        
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}
        self.sequenceListWidget.itemClicked.connect(self.changefig)
        self.addSequenceButton.clicked.connect(self.add_sequence)

        fig = Figure()
        self.addmpl(fig)

        self.plotWidget = PlotWidget()
        self.plotAreaVerticalLayout.addWidget(self.plotWidget)

    def changefig(self, item):
        text = item.text()
        self.rmmpl()
        self.addmpl(self.fig_dict[text])

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    def add_sequence(self):
        self.filename = QtGui.QFileDialog.getOpenFileNames(
            self,
            "Open Sequence Encoder Log",
            "/home/ient/Software/rd-plot-gui/examplLogs",
            "Enocder Logs (*.log)")

        # extract folder and filename
        [directory, file_name] = self.filename[0].rsplit('/',1)
        # extract the part of the filename that files for different QPs share.
        sequence_name_common = file_name.rsplit('_QP',1)[0]
        sequence_files = glob(directory + '/' + sequence_name_common + '*')
        sequence = Sequence(sequence_name_common, sequence_files)
        pass


    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.plotAreaVerticalLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, 
                self.plotAreaWidget, coordinates=True)
        self.plotAreaVerticalLayout.addWidget(self.toolbar)
# This is the alternate toolbar placement. Susbstitute the three lines above
# for these lines to see the different look.
#        self.toolbar = NavigationToolbar(self.canvas,
#                self, coordinates=True)
#        self.addToolBar(self.toolbar)

    def rmmpl(self,):
        self.plotAreaVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.plotAreaVerticalLayout.removeWidget(self.toolbar)
        self.toolbar.close()


class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, ):
        super(PlotWidget, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}
        # self.sequenceListWidget.itemClicked.connect(self.changefig)
        # self.addSequenceButton.clicked.connect(self.add_sequence)

        fig = Figure()
        self.addmpl(fig)

    def changefig(self, item):
        text = item.text()
        self.rmmpl()
        self.addmpl(self.fig_dict[text])

    def addfig(self, name, fig):
        self.fig_dict[name] = fig
        self.sequenceListWidget.addItem(name)

    def add_sequence(self):
        self.filename = QtGui.QFileDialog.getOpenFileNames(
            self,
            "Open Sequence Encoder Log",
            "/home/ient/Software/rd-plot-gui/examplLogs",
            "Enocder Logs (*.log)")

        # extract folder and filename
        [directory, file_name] = self.filename[0].rsplit('/', 1)
        # extract the part of the filename that files for different QPs share.
        sequence_name_common = file_name.rsplit('_QP', 1)[0]
        sequence_files = glob(directory + '/' + sequence_name_common + '*')
        sequence = Sequence(sequence_name_common, sequence_files)
        pass

    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.verticalLayout.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.verticalLayout.addWidget(self.toolbar)

    # This is the alternate toolbar placement. Susbstitute the three lines above
    # for these lines to see the different look.
    #        self.toolbar = NavigationToolbar(self.canvas,
    #                self, coordinates=True)
    #        self.addToolBar(self.toolbar)

    def rmmpl(self, ):
        self.plotAreaVerticalLayout.removeWidget(self.canvas)
        self.canvas.close()
        self.plotAreaVerticalLayout.removeWidget(self.toolbar)
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
        self.sequence_files = {} # will fill this with the list sequence_files with qp as key after they are extracted
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
                print('No match for QP value in sequence name') # todo: notify user, exception?


    def extract_rd_vals(self):
        for (qp, file) in self.sequence_files.items():

            with open(file,'r') as log_file:
                log_text = log_file.read()  # reads the whole text file
                # re.search(r"""^SUMMARY.*$' # catch summary line
                #         # bla
                #     """, log_text, re.M+re.X).group()
                # re.search(r"""  ^SUMMARY.*$ # catch summary line
                #                 \n # catch newline
                #                 \s*(Total Frames)
                #            """, log_text, re.M + re.X).group()
                # re.search(r"""  ^SUMMARY.*$ # catch summary line
                #                 \s* # catch newline and space
                #                 (.*)\| # catch phrase Total Frames
                #                 (\s*(\S*)){5} # catch rest of the line
                #                 \s* # catch newline and space
                #
                #            """, log_text, re.M + re.X).group()
                #
                # re.findall(r"""  ^(\w*)-*.*$ # catch summary line
                #                \s* # catch newline and space
                #                (.*)\| # catch phrase Total Frames / I / P / B
                #                (\s*(\S*)){5} # catch rest of the line
                #                \s* # catch newline and space
                #                (\d*\s*)\w # catch frame number
                #                (\s*\d*\.\d*){5} # catch the fractional number (rate, PSNRs)
                #           """, log_text, re.M + re.X)

                groups = re.findall(r"""  ^(\w*)-*.*$ # catch summary line
                               \s* # catch newline and space
                               (.*)\| # catch phrase Total Frames / I / P / B
                               (\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)(\s*\S*)# catch rest of the line
                               \s* # catch newline and space
                               (\d*\s*)\w # catch frame number
                               (\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*)(\s*\d*\.\d*) # catch the fractional number (rate, PSNRs)
                          """, log_text, re.M + re.X)

                # a = re.compile(r"""\d +  # the integral part
                #    \.    # the decimal point
                #    \d *  # some fractional digits""", re.X)
                pass


if __name__ == '__main__':
    import sys
    from PyQt4 import QtGui
    import numpy as np

    fig1 = Figure()
    ax1f1 = fig1.add_subplot(111)
    ax1f1.plot(np.random.rand(5))

    fig2 = Figure()
    ax1f2 = fig2.add_subplot(121)
    ax1f2.plot(np.random.rand(5))
    ax2f2 = fig2.add_subplot(122)
    ax2f2.plot(np.random.rand(10))

    fig3 = Figure()
    ax1f3 = fig3.add_subplot(111)
    ax1f3.pcolormesh(np.random.rand(20,20))

    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.addfig('One plot', fig1)
    main.addfig('Two plots', fig2)
    main.addfig('Pcolormesh', fig3)
    main.show()
    sys.exit(app.exec_())

