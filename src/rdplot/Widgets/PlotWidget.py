##################################################################################################
#    This file is part of RDPlot - A gui for creating rd plots based on pyqt and matplotlib
#    <https://git.rwth-aachen.de/IENT-Software/rd-plot-gui>
#    Copyright (C) 2017  Institut fuer Nachrichtentechnik, RWTH Aachen University, GERMANY
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##################################################################################################
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.figure import Figure
from matplotlib import cbook
from scipy import spatial

from matplotlib import cycler
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from tikzplotlib import save as tikz_save

import numpy as np
import math
from os.path import sep
import matplotlib.pyplot as plt
from matplotlib.pyplot import show


import pkg_resources

Ui_name = pkg_resources.resource_filename('rdplot', 'ui' + sep + 'plotWidget.ui')
Ui_PlotWidget, QWidget = loadUiType(Ui_name)

class PlotWidget(QWidget, Ui_PlotWidget):
    def __init__(self, ):
        super(PlotWidget, self).__init__()
        self.setupUi(self)
        self.fig_dict = {}

        # store copies of call backs, so that they are not garbage collected
        self.on_wheel_cpy = self.on_wheel
        self.on_db_click_cpy = self.on_db_click

        # set figure and background to transparent
        self.plotAreaWidget.fig = Figure(facecolor="white")
        self.plotAreaWidget.fig.set_tight_layout(True)

        # set some properties for canvas
        self.plotAreaWidget.canvas = FigureCanvas(self.plotAreaWidget.fig)
        self.splitter.setSizes([680, 50])

        self.ax = self.plotAreaWidget.fig.add_subplot(111)
        self.ax.grid(True)

        # connect scroll and double click event to canvas
        self.plotAreaWidget.canvas.mpl_connect('scroll_event', self.on_wheel_cpy)
        self.plotAreaWidget.canvas.mpl_connect('button_press_event', self.on_db_click_cpy)

        self.verticalLayout_3.addWidget(self.plotAreaWidget.canvas)
        # add the toolbar for the plot
        self.toolbar = NavigationToolbar(self.plotAreaWidget.canvas,
                                         self.plotAreaWidget, coordinates=True)
        self.toolbar.pan()
        self.verticalLayout_3.addWidget(self.toolbar)

        self.label_warning.hide()

    def create_legend(self, plot_data_collection):
        tmp_legend = []
        for plot_data in plot_data_collection:
            tmp = []
            for identifiers in plot_data.identifiers:
                tmp += identifiers.split(sep)
            tmp2 = tmp + plot_data.path
            tmp_legend.append(tmp2)

        legend = []
        for c in tmp_legend:
            result = list(filter(lambda x: all(x in l for l in tmp_legend) == False, c))
            legend.append(" ".join(result))
        if len(tmp_legend) == 1:
            legend = ['']

        return legend

    # refreshes the figure according to new changes done
    def change_plot(self, plot_data_collection, user_generated_curves=False):
        """Plot all data from the *plot_data_collection*

        :param plot_data_collection: A iterable collection of :clas: `PlotData`
            objects, which should be plotted.
            temporal data
        """

        if len(plot_data_collection) == 0:
            self._clear_plot()
            return

        if len(plot_data_collection) > 10:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Your selection intends to plot more that 10 curves, do you really want to continue?")
            msg.setWindowTitle("Info")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec()

            if result == QMessageBox.Cancel:
                return

        self.ax.clear()
        self.ax.grid(True)
        self.ax.set_prop_cycle(cycler('color', ['r', 'b', 'y', 'k', 'c', 'm', 'g', 'r', 'b', 'y', 'k', 'c', 'm', 'g']) +
                               cycler('marker', ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'o', 'o', 'o', 'o', 'o', 'o', 'o']))

        self.ax.set_xlabel(plot_data_collection[0].label[0])
        self.ax.set_ylabel(plot_data_collection[0].label[1])

        # Now lets create a legend only containing informative
        # content (no duplicates)
        if not user_generated_curves:
            tmp_legend = []
            for plot_data in plot_data_collection:
                tmp = []
                for identifiers in plot_data.identifiers:
                    tmp += identifiers.split(sep)
                tmp2 = tmp + plot_data.path
                tmp_legend.append(tmp2)

            legend = []
            for c in tmp_legend:
                result = list(filter(lambda x: all(x in l for l in tmp_legend) == False, c))
                legend.append(" ".join(result))
            if len(tmp_legend) == 1:
                legend = ['']
        else:
            # when user-generated curves are involved the legend tends to break the layout and makes the plot impossible
            # to read. therefore only the first identifier is being shown in the legend
            legend = []
            for plot_data in plot_data_collection:
                legend.append(plot_data.identifiers[0])

        # plot all the lines which are missing yet
        plot_count = 0
        for plot_data in plot_data_collection:
            # Create legend from variable path and sim data items identifiers
            l = legend[plot_count] #" ".join([i for i in plot_data.identifiers] + plot_data.path)

            # Convert list of pairs of strings to two sorted lists of floats
            values = ((float(x), float(y)) for (x, y) in plot_data.values)
            sorted_value_pairs = sorted(values, key=lambda pair: pair[0])
            [xs, ys] = list(zip(*sorted_value_pairs))

            # plot the current plotdata and set the legend
            curve = self.ax.plot(xs, ys, label=l)

            plot_count += 1

        if not(legend == ['']):
            self.ax.legend(loc='lower right')
        DataCursor(self.ax.get_lines())

        start, end = self.ax.get_ylim()
        start = math.floor(start)
        end = math.ceil(end)
        if abs(start-end)<20:
            self.ax.yaxis.set_ticks(np.arange(start, end, 0.5))

        self.plotAreaWidget.canvas.draw()

    def export_plot_tikz(self):
        filename, extension = QFileDialog.getSaveFileName(self, 'Save Plot as Tikzpicture', '.', 'Latex (*.tex)')
        if filename != '':      
            if '.tex' not in filename:
                filename += '.tex'          
            tikz_save(filename,self.plotAreaWidget.fig)

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

    def _clear_plot(self):
        self.ax.clear()
        self.ax.grid(True)
        self.plotAreaWidget.canvas.draw()


class DataCursor(object):
    """A simple data cursor widget that displays the x,y location of a
    matplotlib artist when it is selected.
    This is according to http://stackoverflow.com/questions/4652439/is-there-a-matplotlib-equivalent-of-matlabs-datacursormode"""
    def __init__(self, artists, tolerance=5, offsets=(-20, 20),
                 template='rate: %0.2f\npsnr: %0.2f', display_all=True):
        """Create the data cursor and connect it to the relevant figure.
        "artists" is the matplotlib artist or sequence of artists that will be
            selected.
        "tolerance" is the radius (in points) that the mouse click must be
            within to select the artist.
        "offsets" is a tuple of (x,y) offsets in points from the selected
            point to the displayed annotation box
        "template" is the format string to be used. Note: For compatibility
            with older versions of python, this uses the old-style (%)
            formatting specification.
        "display_all" controls whether more than one annotation box will
            be shown if there are multiple axes.  Only one will be shown
            per-axis, regardless.
        """
        self.template = template
        self.offsets = offsets
        self.display_all = display_all
        if not cbook.iterable(artists):
            artists = [artists]
        self.artists = artists
        self.axes = tuple(set(art.axes for art in self.artists))
        self.figures = tuple(set(ax.figure for ax in self.axes))

        self.annotations = {}
        for ax in self.axes:
            self.annotations[ax] = self.annotate(ax)

        for artist in self.artists:
            artist.set_picker(tolerance)
        for fig in self.figures:
            fig.canvas.mpl_connect('pick_event', self)

    def annotate(self, ax):
        """Draws and hides the annotation box for the given axis "ax"."""
        annotation = ax.annotate(self.template, xy=(0, 0), ha='right',
                xytext=self.offsets, textcoords='offset points', va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
                )
        annotation.set_visible(False)
        return annotation

    def __call__(self, event):
        """Intended to be called through "mpl_connect"."""
        # Rather than trying to interpolate, just display the clicked coords
        # This will only be called if it's within "tolerance", anyway.
        x, y = event.mouseevent.xdata, event.mouseevent.ydata
        #catch the closest data point
        x,y = event.artist.get_xydata()[spatial.KDTree(event.artist.get_xydata()).query(np.array([x, y]))[1]]
        annotation = self.annotations[event.artist.axes]
        if x is not None:
            if not self.display_all:
                # Hide any other annotation boxes...
                for ann in self.annotations.values():
                    ann.set_visible(False)
            # Update the annotation in the current axis..
            annotation.xy = x, y
            annotation.set_text(self.template % (x, y))
            annotation.set_visible(True)
            event.canvas.draw()

class BDPlotWidget(PlotWidget):
    def __init__(self, seq=''):
        super(BDPlotWidget, self).__init__()
        self._seq = seq
        self._legend = []

        self.check_open_fig()
        plt.ion()
        self.plotAreaWidget.fig = plt.figure(self._seq)
        self.plotAreaWidget.canvas = self.plotAreaWidget.fig.canvas
        self.toolbar = self.plotAreaWidget.canvas.manager.toolbar
        self.toolbar.pan('on')

        self.plotAreaWidget.fig.canvas.mpl_connect('scroll_event', self.on_wheel_cpy)
        self.plotAreaWidget.canvas.mpl_connect('button_press_event', self.on_db_click_cpy)

    def check_open_fig(self):
        # checks if other bd plots are open and closes them
        labels = plt.get_figlabels()
        if self._seq not in labels: plt.close()

    def create_legend(self, d):
        tmp_legend = []
        for data in d:
            tmp = []
            tmp += data.split(sep)
            tmp_legend.append(tmp)

        legend = []
        for c in tmp_legend:
            result = list(filter(lambda x: all(x in l for l in tmp_legend) == False, c))
            if result: legend.append("".join(result[0]))
        #if len(tmp_legend) == 1:
        #   legend = ['']

        if len(legend) == 2:
            self._legend = legend

    def bd_plot_drate(self, p1, p2, xi1, xi2, min_int, max_int, y1min, y1max, y2min, y2max, rate1, psnr1, rate2, psnr2,
                      avg_diff):

        handles, legend = plt.axes().get_legend_handles_labels()
        if (self._legend[0] + ' original') not in legend:
            plt.plot(p1, xi1, label=self._legend[0] + ' interpolated')
            plt.hlines(min_int, y1min, y2min)
            plt.scatter(rate1, psnr1, label=self._legend[0] + ' original')
        if (self._legend[1] + ' original') not in legend:
            plt.plot(p2, xi2, label=self._legend[1] + ' interpolated ')
            plt.hlines(max_int, y1max, y2max)
            plt.scatter(rate2, psnr2, label=self._legend[1] + ' original')

        plt.legend(loc='upper left')

        plt.xlabel('Rate')
        plt.ylabel('PSNR [dB]')

        plt.grid('on')

        suptitle = u'\u0394 Rate = {diff} %'.format(diff=round(avg_diff, 3))
        plt.suptitle(suptitle)

        show(block=False)

    def bd_plot_dsnr(self, p1, p2, xi1, xi2, min_int, max_int, y1min, y1max, y2min, y2max, x1, x2, y1, y2, avg_diff):

        handles, legend = plt.axes().get_legend_handles_labels()

        if (self._legend[0] + ' original') not in legend:
            plt.plot(xi1, p1, label=self._legend[0] + ' interpolated')
            plt.vlines(min_int, y1min, y2min)
            plt.scatter(x1, y1, label=self._legend[0] + ' original')

        if (self._legend[1] + ' original') not in legend:
            plt.plot(xi2, p2, label=self._legend[1] + ' interpolated')
            plt.vlines(max_int, y1max, y2max)
            plt.scatter(x2, y2, label=self._legend[1] + ' original')

        plt.legend(loc='upper left')

        plt.xlabel('Rate')
        plt.ylabel('PSNR [dB]')

        plt.grid('on')

        suptitle = u'\u0394 PSNR = {diff}'.format(diff=avg_diff)
        plt.suptitle(suptitle)

        show(block=False)