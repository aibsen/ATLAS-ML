#!/usr/bin/env python
"""Run the Keras/Tensorflow classifier.

Usage:
  %s <configFile> [--hkoclassifier=<hkoclassifier>] [--mloclassifier=<mloclassifier>] [--outputsql=<outputsql>] [--listid=<listid>] [--imageroot=<imageroot>]
  %s (-h | --help)
  %s --version

Options:
  -h --help                          Show this screen.
  --version                          Show version.
  --listid=<listid>                  List ID [default: 4].
  --hkoclassifier=<hkoclassifier>    HKO Classifier file.
  --mloclassifier=<mloclassifier>    MLO Classifier file.
  --outputsql=<outputsql>            Output file [default: /tmp/update_eyeball_scores.sql].
  --imageroot=<imageroot>            Root location of the actual images [default: /localhost/images/].


"""
import sys
__doc__ = __doc__ % (sys.argv[0], sys.argv[0], sys.argv[0])
from docopt import docopt
from gkutils import Struct, cleanOptions, readGenericDataFile, dbConnect
import sys, csv, os
from TargetImage import *
import numpy as np
from kerasTensorflowClassifier import create_model, load_data
from collections import defaultdict, OrderedDict

def getATLASImageDataToCheck(conn, dbName, listId = 4, imageRoot='/psdb3/images/'):
    # First get the candidates
    import MySQLdb
    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select id
              from atlas_diff_objects
             where detection_list_id = %s
               and zooniverse_score is null
        """, (listId,))
        resultSet = cursor.fetchall ()


    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    images = []
    # Now, for each candidate, get the image
    for row in resultSet:
        try:
            cursor = conn.cursor (MySQLdb.cursors.DictCursor)
            cursor.execute ("""
            select concat(%s ,%s,'/',truncate(mjd_obs,0), '/', image_filename,'.fits') filename from tcs_postage_stamp_images
             where image_filename like concat(%s, '%%')
               and image_filename not like concat(%s, '%%4300000000%%')
               and image_type = 'diff'
               and image_filename is not null
               and pss_error_code = 0
               and mjd_obs is not null
            """, (imageRoot, dbName, row['id'], row['id']))
            imageResultSet = cursor.fetchall ()
            cursor.close ()
            for row in imageResultSet:
                # Only append images that actually exist!
                if os.path.exists(row['filename']):
                    images.append(row)

        except MySQLdb.Error as e:
            print("Error %d: %s" % (e.args[0], e.args[1]))

    return images


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


def main():
    opts = docopt(__doc__, version='0.1')
    opts = cleanOptions(opts)

    # Use utils.Struct to convert the dict into an object for compatibility with old optparse code.
    options = Struct(**opts)

    import yaml
    with open(options.configFile) as yaml_file:
        config = yaml.load(yaml_file)

    username = config['databases']['local']['username']
    password = config['databases']['local']['password']
    database = config['databases']['local']['database']
    hostname = config['databases']['local']['hostname']

    conn = dbConnect(hostname, username, password, database)
    if not conn:
        print("Cannot connect to the database")
        return 1

    imageFilenames = getATLASImageDataToCheck(conn, database, listId = int(options.listid), imageRoot=options.imageroot)
    print(imageFilenames)

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

    #hkoClassifier = '/home/kws/keras/hko_57966_20x20_skew3_signpreserve_f77475b232425.model.best.hdf5'
    #mloClassifier = '/home/kws/keras/atlas_mlo_57925_20x20_skew3_signpreserve_f331184b993662.model.best.hdf5'

    objectDictHKO = getRBValues(hkoFilenames, options.hkoclassifier)
    objectDictMLO = getRBValues(mloFilenames, options.mloclassifier)

    # Now we have two dictionaries. Combine them.

    objectScores = {}

    for k, v in list(objectDictHKO.items()):
        objectScores[k] = {'hko': np.array(v)}
    for k, v in list(objectDictMLO.items()):
        objectScores[k] = {'mlo': np.array(v)}

    # Some objects will have data from two telescopes, some only one.
    # If we have data from two telescopes, choose the median value of the longest length list.

    print(objectScores)

    return

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
    with open(options.outputsql, 'w') as f:
        for k, v in list(finalScoresSorted.items()):
            print((k, finalScoresSorted[k]))
            f.write("update atlas_diff_objects set zooniverse_score = %f where id = %s;\n" % (finalScoresSorted[k], k))

    conn.close()


if __name__=='__main__':
    main()
