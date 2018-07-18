# ATLAS-ML
Automatic classification of ATLAS objects

To set up:

- create virtual environment with python 3.6 and activate it
- pip install -r requirements.txt

How does it work?

-**getATLASTrainingSetCutouts.py**: It takes as input a config file, a timeframe (mjdMin and mjdMax) and a directory to store the output in. It connects to the ATLAS database using the credentials in the config file and gets all exposures for the given time frame. For each exposure it creates a .txt file containing all x,y positions for the objects in the images. It also creates a 40x40 pixels cutout image for each object.



