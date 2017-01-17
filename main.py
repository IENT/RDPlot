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
                   sort_dict_of_lists_by_key, OrderedDictModel,
                   VariableTreeModel, dict_tree_from_enc_logs)
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
        self.encoderLogTreeModel = EncoderLogTreeModel(is_summary_enabled=True)
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
        self.selectedEncoderLogListModel.items_changed.connect(
            self.update_variable_tree
        )

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

        self.summaryPlotButton.toggled.connect( self.update_plot_type )


        self.variableTreeModel = VariableTreeModel()
        self.variableTreeView.setModel( self.variableTreeModel )

        # Set recursive selection model for variable view
        self._variable_tree_selection_model = QRecursiveSelectionModel(
            self.variableTreeView.model()
        )
        self.variableTreeView.setSelectionModel(
            self._variable_tree_selection_model
        )

        #
        self._variable_tree_selection_model.selectionChanged.connect(
            self.update_plot
        )

        self.encoderLogTreeView.deleteKey.connect(self.remove)

    def remove(self):
        values = self.selectedEncoderLogListModel.values()
        #List call necessary to avoid runtime error because of elements changing
        #during iteration
        self.encoderLogTreeModel.remove( list( values ) )

    def change_list(self, q_selected, q_deselected):
        """Extend superclass behavior by automatically adding the values of
           all selected items in :param: `q_selected` to value list model. """

        selected_q_indexes = q_deselected.indexes()

        q_reselect_indexes = []
        for q_index in self.encoderLogTreeView.selectedIndexes():
            if q_index not in selected_q_indexes:
                q_reselect_indexes.append( q_index )

        # Find all all values that are contained by selected tree items
        tuples = []
        for q_index in q_selected.indexes() + q_reselect_indexes:
            # Add values, ie. encoder logs stored at the item, to the list
            # model.
            encoder_logs = q_index.internalPointer().values
            tuples.extend( (e.path, e) for e in encoder_logs )

        # Overwrite all elements in dictionary by selected values
        # Note, that ovrewriting only issues one `updated` signal, and thus,
        # only rerenders the plots one time. Therefore, simply overwriting
        # is much more efficient, despite it would seem, that selectively
        # overwriting keys is.
        self.selectedEncoderLogListModel.clear_and_update_from_tuples( tuples )

    def get_selected_enc_logs(self):
        return [self.selectedEncoderLogListModel[key] for key in self.selectedEncoderLogListModel]

    def get_plot_data_collection_from_selected_variables(self):
        """Get a :class: `dict` with y-variable as key and values as items
        from the current selection of the variable tree.

        :rtype: :class: `dict` of :class: `string` and :class: `list`
        """

        plot_data_collection = []
        for q_index in self.variableTreeView.selectedIndexes():
            item = q_index.internalPointer()
            if len( item.values ) > 0:
                plot_data_collection.extend( item.values )

        return plot_data_collection

    def update_variable_tree(self):
        """Collect all encoder logs currently selected, and create variable
        tree and corresponding data from it.
        """

        enc_logs = self.get_selected_enc_logs()
        dict_trees = dict_tree_from_enc_logs(enc_logs)
        self.variableTreeModel.clear_and_update_from_dict_trees( dict_trees )

    # updates the plot if the type is changed
    def update_plot_type(self, checked):
        self.encoderLogTreeModel.is_summary_enabled = checked

        # TODO enable if selection is implemented
        if len(self.selectedEncoderLogListModel) != 0:
            self.update_plot()

    # updates the plot if the plot variable is changed
    def update_plot(self):
        plot_data_collection = self.get_plot_data_collection_from_selected_variables()

        self.plotPreview.change_plot(
            plot_data_collection,
            self.summaryPlotButton.isChecked()
        )

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
    def change_plot(self, plot_data_collection, is_summary_enabled):
        """Plot all data from the *plot_data_collection*

        :param plot_data_collection: A iterable collection of :clas: `PlotData`
            objects, which should be plotted.
        :param is_summary_enabled: :class: `Bool` if the data is summary  or
            temporal data
        """

        if len( plot_data_collection ) == 0:
            return

        # put a subplot into the figure and set the margins a little bit tighter than the defaults
        # this is some workaround for PyQt similar to tight layout
        fig = Figure()
        axis = fig.add_subplot(111)
        fig.subplots_adjust(left=0.05, right=0.95,
                            bottom=0.1, top=0.95,
                            hspace=0.2, wspace=0.2)



        for plot_data in plot_data_collection:
            # Convert list of pairs of strings to two sorted lists of floats
            values = ( (float(x), float(y)) for (x, y) in plot_data.values)
            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list( zip(*sorted_value_pairs) )

            # Create legend from variable path and encoder log identifiers
            legend = " ".join(plot_data.identifiers + plot_data.path)

            axis.plot( xs, ys, label=legend )

        # distinguish between summary plot and temporal plot
        # if plotTypeSummary:
        #     axis.set_title('Summary Data')
        #     axis.set_xlabel('Bitrate [kbps]') #TODO is that k bytes or bits? need to check
        #     axis.set_ylabel( + ' [dB]')
        # else:
        #     axis.set_title('Temporal Data')
        #     axis.set_xlabel('POC')
        #     axis.set_ylabel(variable + ' [dB]')

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
