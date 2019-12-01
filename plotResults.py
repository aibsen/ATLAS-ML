#!/usr/bin/env python
"""
Usage:
  %s <csvfile>... [--outputFile=<outputFile>] [--xlim=<xlimit>] [--ylim=<ylimit>]
  %s (-h | --help)
  %s --version

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  --outputFile=<outputFile>    Default place to store the outputfile. [default: /tmp/output.png]
  --xlim=<xlimit>              Plot x limit [default: 1.0]
  --ylim=<ylimit>              Set y limit [default: 1.0]

Example:
  %s output_results.csv
"""
import sys
__doc__ = __doc__ % (sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0])
from docopt import docopt
from gkutils import Struct, cleanOptions
import numpy as np
import pandas as pd
#from sklearn.metrics import roc_curve, auc
from sklearn.metrics import auc
from plotROC import roc_curve
import optparse
import matplotlib.pyplot as plt

def plot_roc(fpr, tpr,roc_auc,roc):
	roc.plot(fpr,tpr,lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
	roc.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
	roc.set_xlabel('False Positive Rate')
	roc.set_ylabel('True Positive Rate')
	roc.set_title('ROC curve')
	roc.legend(loc="lower right")

def plot_tradeoff(mdr, fpr, tradeoff, intercept=[], xlim = 1.0, ylim = 1.0, title = 'Detection Error Tradeoff'):
	tradeoff.plot(mdr,fpr,lw=2)
	if len(intercept) > 0:
		tradeoff.plot([0,intercept[0],intercept[0],intercept[0]], [intercept[1],intercept[1],intercept[1],0], color='black', linestyle='--')
	tradeoff.set_xlabel('Missed detection rate')
	tradeoff.set_ylabel('False positive rate')
	tradeoff.set_title(title)
	#tradeoff.set_xlim(0,0.25)
	#tradeoff.set_ylim(0,0.2)
	tradeoff.set_xlim(0,xlim)
	tradeoff.set_ylim(0,ylim)


def plotResults(files, outputfile, options = None):
	#fig, (roc, tradeoff) = plt.subplots(1,2,sharey=False)
	fig, (tradeoff) = plt.subplots(1,1,sharey=False)
	for file in files:
		data = pd.read_csv(file, names=['file', 'tag', 'prediction'])
		y = data['tag']
		scores = data['prediction']
		#fpr,tpr,thresholds = roc_curve(y, scores, pos_label=1)
		fpr,tpr,thresholds = roc_curve(np.array(y), np.array(scores))

		mdrSet = 0.04
		fpr_at_mdrSet = (fpr[np.where(1-tpr<=mdrSet)[0]][-1])

		print("[+]%.3lf%% mdr gives " % (mdrSet*100) + str(fpr[np.where(1-tpr<=mdrSet)[0]][-1]*100) + "% fpr")
		print("   [+] threshold : %.3lf"%(thresholds[np.where(1-tpr<=mdrSet)[0]][-1]))
		roc_auc = auc(fpr, tpr)	
		mdr = 1-tpr
		plot_tradeoff(mdr, fpr, tradeoff, intercept=[mdrSet,fpr_at_mdrSet], xlim = float(options.xlim), ylim = float(options.ylim), title = 'Detection Error Tradeoff (MLO)')
		#plot_roc(fpr,tpr,roc_auc,roc)
#	plt.savefig(outputfile)
	plt.show()


def main():
    opts = docopt(__doc__, version='0.1')
    opts = cleanOptions(opts)

    # Use utils.Struct to convert the dict into an object for compatibility with old optparse code.
    options = Struct(**opts)
    print (options.csvfile)
    plotResults(options.csvfile, options.outputFile, options = options)


if __name__=='__main__':
    main()
    
