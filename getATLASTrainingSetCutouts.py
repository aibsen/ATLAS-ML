#!/usr/bin/env python
"""Use "stampstorm04 to generate "good" and "bad" training set data for Machine Learning.
Note that this code will generate "good" data from known asteroids, and "bad" data from
everything else that has pvr and ptr = 0. This code only works on the database created from
ddc files. Additionally, it currently does NOT attempt to download any missing exposures.
It assumes that all the required exposures are already downloaded.

Usage:
  %s <configFile> [<mjd>...] [--stampSize=<n>] [--stampLocation=<location>] [--test] [--downloadthreads=<threads>] [--stampThreads=<threads>] [--camera=<camera>]
  %s (-h | --help)
  %s --version

Options:
  -h --help                    Show this screen.
  --version                    Show version.
  --test                       Just do a quick test.
  --stampSize=<n>              Size of the postage stamps if requested [default: 40].
  --stampLocation=<location>   Default place to store the stamps. [default: /tmp]
  --camera=<camera>            Which camera [default: 02a]
  --downloadthreads=<threads>  The number of threads (processes) to use [default: 5].
  --stampThreads=<threads>     The number of threads (processes) to use [default: 28].

Example:
  %s ~/config4_readonly.yaml 58362 --stampLocation=/export/raid/db4data1/scratch/kws/training/atlas/hko_58362o
"""
import sys
__doc__ = __doc__ % (sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0])
from docopt import docopt
import os, MySQLdb, shutil, re, csv, subprocess
from gkutils import Struct, cleanOptions, dbConnect, doRsync
from datetime import datetime
from datetime import timedelta
from collections import defaultdict
from gkmultiprocessingUtils import *

STAMPSTORM04 = "/atlas/bin/stampstorm04"
LOG_FILE_LOCATION = '/' + os.uname()[1].split('.')[0] + '/tc_logs/'
LOG_PREFIX_EXPOSURES = 'background_exposure_downloads'

def getKnownAsteroids(conn, camera, mjd, pkn = 900):
    """
    Get the asteroids.
    """
    import MySQLdb

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select distinct m.obs, d.x, d.y, d.mag, d.dmag, d.ra, d.dec
              from atlas_detectionsddc d, atlas_metadataddc m
             where m.id = d.atlas_metadata_id
               and m.obs like concat(%s, '%%')
               and m.mjd > %s
               and m.mjd < %s
               and d.pkn > %s
               and d.det = 0
               and d.mag > 0.0
          order by m.obs
        """, (camera, mjd, mjd + 1, pkn))
        resultSet = cursor.fetchall ()

        cursor.close ()

    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    return resultSet


def getJunk(conn, camera, mjd):
    """
    Get the garbage.
    """
    import MySQLdb

    try:
        cursor = conn.cursor (MySQLdb.cursors.DictCursor)

        cursor.execute ("""
            select distinct m.obs, d.x, d.y, d.mag, d.dmag, d.ra, d.dec
              from atlas_detectionsddc d, atlas_metadataddc m
             where m.id = d.atlas_metadata_id
               and m.obs like concat(%s, '%%')
               and m.mjd > %s
               and m.mjd < %s
               and d.pvr = 0
               and d.ptr = 0
               and d.pkn = 0
               and d.det = 0
               and d.mag > 0.0
          order by m.obs
        """, (camera, mjd, mjd+1))
        resultSet = cursor.fetchall ()

        cursor.close ()

    except MySQLdb.Error as e:
        print("Error %d: %s" % (e.args[0], e.args[1]))

    return resultSet


def stampStormWrapper(exposureList, stampSize, stampLocation, objectType='good'):

    for exp in exposureList:
        camera = exp[0:3]
        mjd = exp[3:8]
        imageName = '/atlas/diff/' + camera + '/' + mjd + '/' + exp + '.diff.fz'
        #inFile = stampLocation + '/' + objectType + exp + '.txt'
        # The code changes directory to the one below where the text files have been generated.
        # stampstorm04 can't deal with filenames longer than 80 characters, so use a relative
        # directory filename instead
        inFile = '../' + objectType + exp + '.txt'

        if objectType == 'good':
            goodDir = stampLocation+'/good'
            if not os.path.exists(goodDir):
                print("creating"+goodDir)
                try:
                    os.makedirs(goodDir)
                except FileExistsError as e:
                    pass
            os.chdir(goodDir)

        else:
            badDir = stampLocation+'/bad'
            if not os.path.exists(badDir):
                try:
                    os.makedirs(badDir)   
                except FileExistsError as e:
                    pass
            os.chdir(badDir)

        p = subprocess.Popen([STAMPSTORM04, inFile, imageName, objectType, str(stampSize/2)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()

        if output.strip():
            print(output)
        if errors.strip():
            print(errors)

    return


def workerImageDownloader(num, db, listFragment, dateAndTime, firstPass, miscParameters):
    """thread worker function"""
    # Redefine the output to be a log file.
    sys.stdout = open('%s%s_%s_%d.log' % (LOG_FILE_LOCATION, LOG_PREFIX_EXPOSURES, dateAndTime, num), "w")

    # Call the postage stamp downloader
    objectsForUpdate = doRsync(listFragment, miscParameters[0])
    print ("Process complete.")
    return 0


def workerStampStorm(num, db, listFragment, dateAndTime, firstPass, miscParameters):
    """thread worker function"""
    # Redefine the output to be a log file.
    sys.stdout = open('%s%s_%s_%d.log' % (LOG_FILE_LOCATION, LOG_PREFIX_EXPOSURES, dateAndTime, num), "w")

    stampStormWrapper(listFragment, miscParameters[0], miscParameters[1], objectType = miscParameters[2])    

    print("Process complete.")
    return 0 


# 2018-09-04 KWS Make sure the tiles files do not get written into the good.txt and bad.txt files.
def getGoodBadFiles(path):
       
    with open(path+'/good.txt', 'w') as good:
            for file in os.listdir(path+'/good'):
                if 'tiles' not in file:
                    good.write(file+'\n')

    with open(path+'/bad.txt', 'w') as bad:
            for file in os.listdir(path+'/bad'):
                if 'tiles' not in file:
                    bad.write(file+'\n')
    print("Generated good and bad files")


def getATLASTrainingSetCutouts(opts):
    if type(opts) is dict:
        options = Struct(**opts)
    else:
        options = opts

    import yaml
    with open(options.configFile) as yaml_file:
        config = yaml.load(yaml_file)

    stampSize = int(options.stampSize)
    mjds = options.mjd
    if not mjds:
        print ("No MJDs specified")
        return 1

    downloadThreads = int(options.downloadthreads)
    stampThreads = int(options.stampThreads)
    stampLocation = options.stampLocation
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

    currentDate = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
    (year, month, day, hour, min, sec) = currentDate.split(':')
    dateAndTime = "%s%s%s_%s%s%s" % (year, month, day, hour, min, sec)

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

        print("%s Parallel Processing Good objects..." % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
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

        print("%s Parallel Processing Bad objects..." % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
        parallelProcess([], dateAndTime, nProcessors, listChunks, workerStampStorm, miscParameters = [stampSize, stampLocation, 'bad'], drainQueues = False)
        print("%s Done Parallel Processing" % (datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S")))
    
    conn.close()
    getGoodBadFiles(stampLocation)


def main():
    opts = docopt(__doc__, version='0.1')
    opts = cleanOptions(opts)

    # Use utils.Struct to convert the dict into an object for compatibility with old optparse code.
    options = Struct(**opts)
    getATLASTrainingSetCutouts(options)


if __name__=='__main__':
    main()
    
