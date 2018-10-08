#   Copyright 2014.
#   Institut fuer Nachrichtentechnik
#   RWTH Aachen University
#   All Rights Reserved.

import math
from  math import log10

from rdplot.Widgets.PlotWidget import BDPlotWidget

import numpy as np
from scipy.interpolate import pchip
from scipy import integrate

def bdrint(rate, dist, low, high):
    log_rate = sorted([log10(t) for t in rate])
    log_dist = sorted(dist)

    h = [0] * 3
    delta = [0] * 3
    for i in range(0, 3):
        h[i] = log_dist[i + 1] - log_dist[i]
        delta[i] = (log_rate[i + 1] - log_rate[i]) / h[i]

    d = [0] * 4
    d[0] = ((2 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
    if d[0] * delta[0] < 0:
        d[0] = 0
    for i in range(1, 3):
        d[i] = (3 * h[i - 1] + 3 * h[i]) / ((2 * h[i] + h[i - 1]) / delta[i - 1] + (h[i] + 2 * h[i - 1]) / delta[i])
    d[3] = ((2 * h[2] + h[1]) * delta[2] - h[2] * delta[1]) / (h[2] + h[1])
    if d[3] * delta[2] < 0:
        d[3] = 0

    c = [0] * 3
    b = [0] * 3
    for i in range(0, 3):
        c[i] = (3 * delta[i] - 2 * d[i] - d[i + 1]) / h[i]
        b[i] = (d[i] - 2 * delta[i] + d[i + 1]) / (h[i] * h[i])

    '''
    cubic function is rate(i) + s*(d(i) + s*(c(i) + s*(b(i))) where s = x - dist(i)
    or rate(i) + s*d(i) + s*s*c(i) + s*s*s*b(i)
    primitive is s*rate(i) + s*s*d(i)/2 + s*s*s*c(i)/3 + s*s*s*s*b(i)/4
    '''
    result = 0

    for i in range(0, 3):
        s0 = max(log_dist[i], low) - log_dist[i]
        s1 = min(log_dist[i + 1], high) - log_dist[i]

        result += (s1 - s0) * log_rate[i]
        result += (s1 * s1 - s0 * s0) * d[i] / 2
        result += (s1 * s1 * s1 - s0 * s0 * s0) * c[i] / 3
        result += (s1 * s1 * s1 * s1 - s0 * s0 * s0 * s0) * b[i] / 4

    return result


# function for bjontegaard
def bdrateStd(rate1, dist1, rate2, dist2):
    min_psnr = max(min(dist1), min(dist2))
    max_psnr = min(max(dist1), max(dist2))

    v_a = bdrint(rate1, dist1, min_psnr, max_psnr)
    v_b = bdrint(rate2, dist2, min_psnr, max_psnr)

    avg = (v_b - v_a) / (max_psnr - min_psnr)

    bdrate = (10 ** avg - 1) * 100

    return bdrate


def bdsnr(rate1, psnr1, rate2, psnr2, interpol, seq, directories, testmode):
    """"
    take parameters of 2 lines with some configuration and calculate bjontegaard statistics

    """

    # integration interval
    min_int = max([min(rate1), min(rate2)])
    max_int = min([max(rate1), max(rate2)])

    xi1 = np.linspace(rate1[0], rate1[-1], 100)
    xi2 = np.linspace(rate2[0], rate2[-1], 100)

    # point to plot area between 2 curves
    tmpx1 = [x for x in xi1 if min_int <= x <= max_int]
    tmpx2 = [x for x in xi2 if min_int <= x <= max_int]
    tmpx = tmpx1
    tmpx.extend(tmpx2)
    tmpx = np.array(sorted(tmpx))

    # convert input lists in numpy arrays
    x1 = np.array(rate1)
    y1 = np.array(psnr1)
    x2 = np.array(rate2)
    y2 = np.array(psnr2)

    if interpol == 'pol':
        pv = lambda p, v: np.polyval(p, v)

        pp1 = np.polyfit(x1, y1, 3)
        pp2 = np.polyfit(x2, y2, 3)

        def find_diff(poly1, poly2, max_int, min_int):
            # find integral
            p_int1 = np.polyint(poly1)
            p_int2 = np.polyint(poly2)

            int1 = pv(p_int1, max_int) - pv(p_int1, min_int)
            int2 = pv(p_int2, max_int) - pv(p_int2, min_int)

            # calculate average difference
            out = (int2 - int1) / (max_int - min_int)

            return out

    elif interpol == 'pchip':
        pv = lambda p, v: p(v)

        pp1 = pchip(x1, y1)
        pp2 = pchip(x2, y2)

        def find_diff(poly1, poly2, max_int, min_int):
            # find integrals
            int1 = integrate.quad(poly1, min_int, max_int)
            int2 = integrate.quad(poly2, min_int, max_int)

            # calculate average difference
            out = (int2[0] - int1[0]) / (max_int - min_int)

            return out
    else:
        print("Wrong interpolation method.")
        return 0

    p1 = pv(pp1, xi1)
    p2 = pv(pp2, xi2)

    ptmp1 = pv(pp1, tmpx)
    ptmp2 = pv(pp2, tmpx)

    # value of function at min and max
    y1min = pv(pp1, min_int)
    y2min = pv(pp2, min_int)
    y1max = pv(pp1, max_int)
    y2max = pv(pp2, max_int)

    avg_diff = find_diff(pp1, pp2, max_int, min_int)

    if not testmode:

        bd = BDPlotWidget(seq)
        bd.create_legend(directories)
        bd.bd_plot_dsnr(p1, p2, xi1, xi2, min_int, max_int, y1min, y1max, y2min, y2max, x1, x2, y1, y2, avg_diff)

    return avg_diff


def brate(rate1, psnr1, rate2, psnr2, interpol, seq, directories, testmode):
    # integration interval
    min_int = max([min(psnr1), min(psnr2)])
    max_int = min([max(psnr1), max(psnr2)])

    xi1 = np.linspace(psnr1[0], psnr1[-1], 100)
    xi2 = np.linspace(psnr2[0], psnr2[-1], 100)

    # point to plot area between 2 curves
    tmpx1 = [x for x in xi1 if min_int <= x <= max_int]
    tmpx2 = [x for x in xi2 if min_int <= x <= max_int]
    tmpx = tmpx1
    tmpx.extend(tmpx2)

    # tmpx = np.array(sorted(tmpx))

    # convert input lists in numpy arrays
    x1 = np.array(rate1)
    y1 = np.array(psnr1)
    x2 = np.array(rate2)
    y2 = np.array(psnr2)

    if interpol == 'pol':
        pv = lambda p, v: np.polyval(p, v)

        pp1 = np.polyfit(psnr1, rate1, 3)
        pp2 = np.polyfit(psnr2, rate2, 3)

        def find_diff(poly1, poly2, max_int, min_int):
            # find integral
            p_int1 = np.polyint(poly1)
            p_int2 = np.polyint(poly2)

            int1 = pv(p_int1, max_int) - pv(p_int1, min_int)
            int2 = pv(p_int2, max_int) - pv(p_int2, min_int)
            # calculate average difference???
            out = (int2 - int1) / (max_int - min_int)

            return out

    elif interpol == 'pchip':
        pv = lambda p, v: p(v)

        pp1 = pchip(y1, x1)
        pp2 = pchip(y2, x2)

        def find_diff(poly1, poly2, max_int, min_int):
            # find integrals
            int1 = integrate.quad(poly1, min_int, max_int)
            int2 = integrate.quad(poly2, min_int, max_int)

            # calculate average difference
            out = (int2[0] - int1[0]) / (max_int - min_int)

            return out
    else:
        print("Wrong interpolation method.")
        return 0

    p1 = pv(pp1, xi1)
    p2 = pv(pp2, xi2)

    '''
    ptmp1 = pv(pp1, tmpx)
    ptmp2 = pv(pp2, tmpx)
    '''

    # calculate average difference in %
    avg_exp_diff = find_diff(pp1, pp2, max_int, min_int)
    avg_diff = (np.exp(avg_exp_diff) - 1) * 100

    # value of function at min and max
    y1min = pv(pp1, min_int)
    y2min = pv(pp2, min_int)
    y1max = pv(pp1, max_int)
    y2max = pv(pp2, max_int)

    if not testmode:
        bd = BDPlotWidget(seq)
        bd.create_legend(directories)
        bd.bd_plot_drate(p1, p2, xi1, xi2, min_int, max_int, y1min, y1max, y2min, y2max, rate1, psnr1, rate2, psnr2,
                         avg_diff)

    return avg_diff


def bjontegaard(curve1, curve2, mode='dsnr', interpol='pol', seq='', d=list(), testmode=False):
    """
    Bjontegaard metric calculation
    Bjontegaard's metric allows to compute the average gain in PSNR or the
    average per cent saving in bitrate between two rate-distortion
    curves.

    curve1,2 :
        Arrays of points (rate, psnr)
        [(rate, psnr), (rate, psnr), ...]

    mode :
       'dsnr' - average PSNR difference
       'rate' - percentage of bitrate saving between data set 1 and
                data set 2
    interpol:
        'pol'   -   third order polynomial interpolation
        'pchip' -   piecewise cubic interpolation


    python version of code written by (c) 2010 Giuseppe Valenzise
    http://www.mathworks.com/matlabcentral/fileexchange/27798-bjontegaard-metric/content/bjontegaard.m

    """

    if interpol not in ['pol', 'pchip']:
        print("Wrong interpolation type was given. Use 'pol' for polynomial and 'pchip' for piecewise cubic " \
              "interpolation.")
        exit(1)

    # sort rate
    curve1 = sorted(curve1, key=lambda tup: tup[1])
    curve2 = sorted(curve2, key=lambda tup: tup[1])

    # convert rates in logarithmic units
    psnr1 = [i[1] for i in curve1]
    rate1 = [math.log(i[0]) for i in curve1]

    psnr2 = [i[1] for i in curve2]
    rate2 = [math.log(i[0]) for i in curve2]

    if mode == 'dsnr':
        return bdsnr(rate1, psnr1, rate2, psnr2, interpol, seq, d, testmode)
    elif mode == 'drate':
        # this branch will never be executed because of line 273
        if interpol == 'pchip4':
            rate1 = [i[0] for i in curve1]
            rate2 = [i[0] for i in curve2]
            return bdrateStd(rate1, psnr1, rate2, psnr2)
        else:
            return brate(rate1, psnr1, rate2, psnr2, interpol, seq, d, testmode)
    else:
        print("Wrong mode was given. Use either 'dsnr' or 'rate' mode.")
        exit(1)


# if __name__ == '__main__':
#     c1 = [(1000, 28.47), (1200, 32.07), (1400, 34.77), (1600, 36.87)]
#     c2 = [(900, 28.9), (1100, 32.5), (1300, 35.2), (1500, 37.3)]
#
#
#
#     c5 = [(400, 30.0), (900, 33.0), (2200, 37.0), (4300.0, 40.0)]
#     c6 = [(497.1448, 33.1964), (1035.6816, 35.6696), (2104.344, 38.492), (4178.4152, 41.4858)]
#
#     dirs = ['first', 'second']
#     print bjontegaard(c1, c2, 'dsnr', 'pchip', 'TEST', dirs,)
#
#
#     # plt.show()
#     # print x




