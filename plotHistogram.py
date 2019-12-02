#!/usr/bin/env python
"""Plot histogram to show performance of the specified trained classifier.

Usage:
  %s <classifierFile> [--outputFile=<file>]
  %s (-h | --help)
  %s --version

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  --outputFile=<file>          Output file. If not defined, show plot.

"""
import sys
__doc__ = __doc__ % (sys.argv[0], sys.argv[0], sys.argv[0])
from docopt import docopt
import os, MySQLdb, shutil, re, csv, subprocess
from gkutils import Struct, cleanOptions, readGenericDataFile
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as n

def plotHistogram(dataSeries):

    lenSeries0 = len(dataSeries[0])
    lenSeries1 = len(dataSeries[1])
    fig = plt.figure()

    ax1 = fig.add_subplot(111)

    bins = n.linspace(0.0,1.0,200)

    ml = MultipleLocator(1.0)
    ax1.xaxis.set_major_locator(ml)

    ax1 = fig.add_subplot(111)
    ax1.hist(n.array(dataSeries[0]), bins=bins, color = 'r', label = "Bad", linewidth=1.0, alpha = 0.5)
    ax1.set_ylabel('Number of Objects')
    for tl in ax1.get_yticklabels():
        tl.set_color('b')

    ax1.hist(dataSeries[1], bins=bins, color='g', label = "Good", linewidth=1.0, alpha = 0.5)

    ax1.set_xlabel('Realbogus Factor')
    #ax1.set_title('Classifier performance.')
    ax1.legend(loc=1)
    ml = MultipleLocator(0.2)
    ax1.xaxis.set_minor_locator(ml)
    ax1.get_xaxis().set_tick_params(which='both', direction='out')
    #ax1.set_xlim(0.0, 3.0)
    ax1.set_xlim(0.0, 1.0)
    ax1.set_ylim(0.0, 6000.0)

    plt.show()
    #plt.savefig(filename + '.png', dpi=600)


def doPlots(options):
    dataRows = readGenericDataFile(options.classifierFile, fieldnames = ['file','label','score'], delimiter=',')

    goods = []
    bads = []
    for row in dataRows:
        if row['label'] == '1':
            goods.append(float(row['score']))
        elif row['label'] == '0':
            bads.append(float(row['score']))

    plotHistogram([bads, goods])


def main():
    opts = docopt(__doc__, version='0.1')
    opts = cleanOptions(opts)
    options = Struct(**opts)

    doPlots(options)


if __name__=='__main__':
    main()


