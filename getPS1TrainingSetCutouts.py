#!/usr/bin/env python
"""Create symlinks to the set of Pan-STARRS training set images.
The cutouts are already done.

Usage:
  %s <configFile> [--stampLocation=<location>] [--test]
  %s (-h | --help)
  %s --version

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  --test                       Just do a quick test.
  --stampLocation=<location>   Default place to store the stamps. [default: /tmp]

"""
import sys
__doc__ = __doc__ % (sys.argv[0], sys.argv[0], sys.argv[0])
from docopt import docopt
import os, MySQLdb, shutil, re, csv, subprocess
from gkutils import Struct, cleanOptions, dbConnect, doRsync
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from gkmultiprocessingUtils import *




# Get the objects we've collected into the attic over the years
# which are labelled as movers by the ephemeric check software

def getGoodPS1Objects(conn, listId):
    """
    Get "good" objects
    """
    import MySQLdb

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select distinct o.id
              from tcs_transient_objects o, tcs_object_comments c
             where o.id = c.transient_object_id
               and detection_list_id = %s
               and observation_status = 'mover'
               and confidence_factor is not null
               and (comment like 'EPH:%%' or comment like 'MPC:%%')
        """, (listId,))
        resultSet = cursor.fetchall ()

        cursor.close ()

    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    return resultSet


def getBadPS1Objects(conn, listId, rbThreshold = 0.1):
    """
    Get "bad" objects
    """
    import MySQLdb

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select distinct o.id
              from tcs_transient_objects o, tcs_object_comments c
             where o.id = c.transient_object_id
               and confidence_factor < %s 
               and detection_list_id = %s
               and (comment like 'EPH:.%' or comment like 'MPC:%%')
        """, (rbThreshold, listId,))
        resultSet = cursor.fetchall ()

        cursor.close ()

    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    return resultSet



def getImagesForObject(conn, objectId):
    """
    Get images for an object.
    """
    import MySQLdb

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select i.image_filename
            from tcs_postage_stamp_images i, tcs_transient_objects o
            where i.image_filename like concat(o.id, '%%')
            and i.image_filename not like concat(o.id, '%%4300000000%%')
            and pss_error_code = 0
            and i.image_type = 'diff'
            and o.id = %s
        """, (objectId,))
        resultSet = cursor.fetchall ()

        cursor.close ()

    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    return resultSet


def getTrainingSetImages(conn, listId, imageHome = '/psdb2/images/'):
    goodObjects = getGoodPS1Objects(conn, listId = 5)

    goodImages = []
    for candidate in goodObjects:
        images = getImagesForObject(conn, candidate['id'])

        for image in images:
            goodImages.append(image['image_filename'])

    badObjects = getBadPS1Objects(conn, listId = 5)
    
    badImages = []
    for candidate in badObjects:
        images = getImagesForObject(conn, candidate['id'])

        for image in images:
            badImages.append(image['image_filename'])


def getGoodBadFiles(path):
       
    with open(path+'/good.txt', 'a') as good:
            for file in os.listdir(path+'/good'):
                    good.write(file+'\n')

    with open(path+'/bad.txt', 'a') as bad:
            for file in os.listdir(path+'/bad'):
                    bad.write(file+'\n')
    print("Generated good and bad files")


def main(argv = None):
    opts = docopt(__doc__, version='0.1')
    opts = cleanOptions(opts)
    options = Struct(**opts)

    import yaml
    with open(options.configFile) as yaml_file:
        config = yaml.load(yaml_file)

    stampLocation = options.stampLocation

    print(stampLocation)

    return
    if not os.path.exists(stampLocation):
        os.makedirs(stampLocation)

    username = config['databases']['local']['username']
    password = config['databases']['local']['password']
    database = config['databases']['local']['database']
    hostname = config['databases']['local']['hostname']

    conn = dbConnect(hostname, username, password, database)
    if not conn:
        print("Cannot connect to the database")
        return 1

    asteroidExpsDict = defaultdict(list)
    for mjd in mjds:
        asteroidExps = getKnownAsteroids(conn, options.camera, int(mjd), pkn = 900)
        for exp in asteroidExps:
            asteroidExpsDict[exp['obs']].append(exp)
    
    # Now create the files.  We need to have x, y as the first two items.

    #m.obs, d.x, d.y, d.mag, d.dmag, d.ra, d.dec
    header="x,y,mag,dmag,ra,dec,obs".split(',')

    exposureList = []
    for k,v in asteroidExpsDict.items():
        exposureList.append(k)
        with open(stampLocation + '/' + 'good' + k + '.txt', 'w') as csvfile:
            w = csv.DictWriter(csvfile, fieldnames=header, delimiter=' ')
            #w.writeheader()
            for row in v:
                w.writerow(row)
    # So now let stampstorm do its stuff

    if len(exposureList) > 0:
        nProcessors, listChunks = splitList(exposureList, bins = stampThreads)

        print("%s Parallel Processing..." % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
        parallelProcess([], dateAndTime, nProcessors, listChunks, workerStampStorm, miscParameters = [stampSize, stampLocation, 'good'], drainQueues = False)
        print("%s Done Parallel Processing" % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))

    junkExpsDict = defaultdict(list)
    for mjd in mjds:
        junkExps = getJunk(conn, options.camera, int(mjd))
        for exp in junkExps:
            junkExpsDict[exp['obs']].append(exp)

    exposureList = []
    for k,v in junkExpsDict.items():
        exposureList.append(k)
        with open(stampLocation + '/' + 'bad' + k + '.txt', 'w') as csvfile:
       	    w = csv.DictWriter(csvfile, fieldnames=header, delimiter=' ')
            #w.writeheader()
            for row in v:
                w.writerow(row)

    if len(exposureList) > 0:
        nProcessors, listChunks = splitList(exposureList, bins = stampThreads)

        print("%s Parallel Processing..." % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
        parallelProcess([], dateAndTime, nProcessors, listChunks, workerStampStorm, miscParameters = [stampSize, stampLocation, 'bad'], drainQueues = False)
        print("%s Done Parallel Processing" % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
    
    conn.close()
    getGoodBadFiles(stampLocation)

if __name__=='__main__':
    main()
    
