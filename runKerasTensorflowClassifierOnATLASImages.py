import sys, csv, os
from gkutils import readGenericDataFile
from TargetImage import *
import numpy as np
from kerasTensorflowClassifier import create_model, load_data
from collections import defaultdict, OrderedDict

def getRBValues(imageFilenames, classifier):
    num_classes = 2
    image_dim = 20
    numImages = len(imageFilenames)
    images = np.zeros((numImages, image_dim,image_dim,1))
    #print images
    # loop through and fill the above matrix, remembering to correctly scale the
    # raw pixels for the specified sparse filter.
    for j,imageFilename in enumerate(imageFilenames):
        vector = np.nan_to_num(TargetImage(imageFilename, extension=0).signPreserveNorm())
        #print vector
        #print vector.shape
        images[j,:,:,0] += np.reshape(vector, (image_dim,image_dim), order="F")

    #print images.shape


    model = create_model(num_classes, image_dim)
    model.load_weights(classifier)

    pred = model.predict(images, verbose=0)
    print(pred)
    # Collect the predictions from all the files, but aggregate into objects
    objectDict = defaultdict(list)
    for i in range(len(pred[:,1])):
        candidate = os.path.basename(imageFilenames[i]).split('_')[0]
        # Each candidate will end up with a list of predictions.
        objectDict[candidate].append(pred[i,1])

        #print "%s,%.3lf"%(imageFilenames[i], pred[i,1])

    return objectDict


def main(argv = None):
    if argv is None:
        argv = sys.argv


    usage = "Usage: %s <filename list>" % argv[0]
    if len(argv) < 2:
        sys.exit(usage)

    filenames = argv[1]
    imageFilenames = readGenericDataFile(filenames, delimiter = ' ')

    # Split the images into HKO and MLO data so we can apply the HKO and MLO machines separately.
    hkoFilenames = []
    for row in imageFilenames:
        if '02a' in row['filename']:
            hkoFilenames.append(row['filename'])
    mloFilenames = []
    for row in imageFilenames:
        if '01a' in row['filename']:
            mloFilenames.append(row['filename'])

    #filename = 'hko_57966_20x20_skew3_signpreserve_f77475b232425.mat'
    #train_data, test_data, image_dim = load_data(filename)
    #x_test = test_data[0]

    hkoClassifier = '/home/kws/keras/hko_57966_20x20_skew3_signpreserve_f77475b232425.model.best.hdf5'
    mloClassifier = '/home/kws/keras/atlas_mlo_57925_20x20_skew3_signpreserve_f331184b993662.model.best.hdf5'

    objectDictHKO = getRBValues(hkoFilenames, hkoClassifier)
    objectDictMLO = getRBValues(mloFilenames, mloClassifier)

    # Now we have two dictionaries. Combine them.

    objectScores = {}

    for k, v in list(objectDictHKO.items()):
        objectScores[k] = {'hko': np.array(v)}
    for k, v in list(objectDictMLO.items()):
        objectScores[k] = {'mlo': np.array(v)}

    # Some objects will have data from two telescopes, some only one.
    # If we have data from two telescopes, choose the median value of the longest length list.

    finalScores = {}

    objects = list(objectScores.keys())
    for object in objects:
        if len(objectScores[object]) > 1:
            hkoLen = len(objectScores[object]['hko'])
            mloLen = len(objectScores[object]['mlo'])
            if mloLen > hkoLen:
                finalScores[object] = np.median(objectScores[object]['mlo'])
            else:
                # Only if MLO is larger than HKO, use MLO. Otherise use HKO
                finalScores[object] = np.median(objectScores[object]['hko'])

        else:
            try:
                finalScores[object] = np.median(objectScores[object]['hko'])
            except KeyError as e:
                finalScores[object] = np.median(objectScores[object]['mlo'])

    finalScoresSorted = OrderedDict(sorted(list(finalScores.items()), key=lambda t: t[1]))

    # Generate the insert statements
    with open("/home/kws/keras/update_eyeball_scores.sql", 'w') as f:
        for k, v in list(finalScoresSorted.items()):
            print((k, finalScoresSorted[k]))
            f.write("update atlas_diff_objects set zooniverse_score = %f where id = %s;\n" % (finalScoresSorted[k], k))



if __name__=='__main__':
    main()
