import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc
import optparse
import matplotlib.pyplot as plt

def plot_roc(fpr, tpr,roc_auc,roc):
	roc.plot(fpr,tpr,lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
	roc.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
	roc.set_xlabel('False Positive Rate')
	roc.set_ylabel('True Positive Rate')
	roc.set_title('ROC curve')
	roc.legend(loc="lower right")

def plot_tradeoff(mdr, fpr, tradeoff):
	tradeoff.plot(mdr,fpr,lw=2)
	tradeoff.set_xlabel('Missed detection rate')
	tradeoff.set_ylabel('False positive rate')
	tradeoff.set_title('Detection Error Tradeoff')


def plotResults(files, outputfile):
	fig, (roc, tradeoff) = plt.subplots(1,2,sharey=True)
	for file in files:
		data = pd.read_csv(file, names=['file', 'tag', 'prediction'])
		y = data['tag']
		#swap tags
		y[y==0] = -1
		y[y==1] = 0
		y[y==-1]= 1
		y = y.values
		scores = data['prediction'].values
		fpr,tpr,thresholds = roc_curve(y, scores, pos_label=0)
		roc_auc = auc(fpr, tpr)	
		mdr = 1-tpr
		plot_tradeoff(mdr, fpr, tradeoff)
		plot_roc(fpr,tpr,roc_auc,roc)
	plt.savefig(outputfile)
	plt.show()

