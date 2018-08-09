# ATLAS-ML
Automatic classification of ATLAS objects

![alt text](/imgs/classification_pipeline.png)
How does it work?

-**getATLASTrainingSetCutouts.py**: It takes as input a config file, a list of dates (in MJD) and a directory to store the output in. It connects to the ATLAS database using the credentials in the config file and gets all exposures for the given time frame. For each exposure it creates a .txt file containing all x,y positions for the objects in the images and a 40x40 pixels cutout image for each object. It also creates a "good.txt" and a "bad.txt" file, containing the x,y positions for the real and 
bogus objects, respectively.

-**getPS1TrainingSetCutouts.py**: Same as the above file, but it connects to the PS1 data base instead.

-**buildMLDataset.py**: It takes as input the good.txt and bad.txt files with all x,y positions for real and bogus objects. From those, it builds an .h5 file containing the features (20x20 pixels of the image) and targets (real or bogus label) to be used later as training set.

-**kerasTensorflowClassifier.py**: It takes as input an .h5 file with the training set and a path to store a classifier as an .h5 file. If the model doesn't exist yet, it creates it, trains it and classifies a test set. It returns a .csv file containing  the targets and scores for all images.

-**plotResults.py**: It takes as input a csv file with the scores and targets for all images and plots the ROC curve and the Detection error tradeoff graph for the data set.


To set up:

- create virtual environment with python 3.6 and activate it
- pip install -r requirements.txt

