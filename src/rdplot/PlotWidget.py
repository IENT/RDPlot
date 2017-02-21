from PyQt5.uic import loadUiType

from matplotlib.figure import Figure
from matplotlib.axis import Axis
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from mpldatacursor import datacursor

import numpy as np
import math
from os.path import sep
import pkg_resources

Ui_name = pkg_resources.resource_filename(__name__, 'ui' + sep + 'plotWidget.ui')
Ui_PlotWidget, QWidget = loadUiType(Ui_name)


class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, ):
        super(PlotWidget, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        # store copies of call backs, so that they are not garbage collected
        self.on_wheel_cpy = self.on_wheel
        self.on_db_click_cpy = self.on_db_click

        # set figure and backgroung to transparent
        self.plotAreaWidget.fig = Figure(facecolor="white")
        self.plotAreaWidget.fig.set_tight_layout(True)

        # set some properties for canvas
        self.plotAreaWidget.canvas = FigureCanvas(self.plotAreaWidget.fig)
        self.splitter.setSizes([680, 50])

        self.ax = self.plotAreaWidget.fig.add_subplot(111)
        self.ax.grid(True)
        self.current_identifiers = []

        # connect scroll and double click event to canvas
        self.plotAreaWidget.canvas.mpl_connect('scroll_event', self.on_wheel_cpy)
        self.plotAreaWidget.canvas.mpl_connect('button_press_event', self.on_db_click_cpy)

        self.verticalLayout_3.addWidget(self.plotAreaWidget.canvas)
        # add the toolbar for the plot
        self.toolbar = NavigationToolbar(self.plotAreaWidget.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.toolbar.pan()
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

        # get the identifiers (in this case legends as they are unique) from plot_data_collection
        identifiers = []
        for plot_data in plot_data_collection:
            # Create legend from variable path and sim data items identifiers
            legend = " ".join([i.split('_', 1)[0] for i in plot_data.identifiers] + plot_data.path)
            identifiers.append(legend)

        # remove all lines which are not wanted anymore
        for curve in self.ax.get_lines():
            if curve.get_label() not in identifiers:
                self.current_identifiers.remove(curve.get_label())
                curve.remove()

        # plot all the lines which are missing yet
        for plot_data in plot_data_collection:
            # Create legend from variable path and sim data items identifiers
            legend = " ".join([i.split('_', 1)[0] for i in plot_data.identifiers] + plot_data.path)
            if legend in self.current_identifiers:
                continue

            # Convert list of pairs of strings to two sorted lists of floats
            values = ((float(x), float(y)) for (x, y) in plot_data.values)
            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list(zip(*sorted_value_pairs))

            # plot the current plotdata and set the legend
            self.ax.plot(xs, ys, '-x', label=legend)
            self.ax.legend(loc='lower right')

            # append legend to current identifiers
            self.current_identifiers.append(legend)

        # set  y tick in 0.5 spacing
        self.ax.relim()
        self.ax.autoscale()

        start, end = self.ax.get_ylim()
        start = math.floor(start)
        end = math.ceil(end)
        self.ax.yaxis.set_ticks(np.arange(start, end, 0.5))

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

        axis.set_xlim([event.xdata - new_width * (1 - rel_x), event.xdata + new_width * rel_x])
        axis.set_ylim([event.ydata - new_height * (1 - rel_y), event.ydata + new_height * rel_y])

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
