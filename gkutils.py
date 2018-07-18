def dbConnect(lhost, luser, lpasswd, ldb, lport=3306, quitOnError=True):
   import MySQLdb

   try:
      conn = MySQLdb.connect (host = lhost,
                              user = luser,
                            passwd = lpasswd,
                                db = ldb,
                              port = lport)
   except MySQLdb.Error as e:
      print("Error %d: %s" % (e.args[0], e.args[1]))
      if quitOnError:
         sys.exit (1)
      else:
         conn=None

   return conn

# 2013-02-04 KWS Create an object from a dictionary.
class Struct:
    """Create an object from a dictionary. Ensures compatibility between raw scripted queries and Django queries."""
    def __init__(self, **entries): 
        self.__dict__.update(entries)

# 2017-11-02 KWS Quick and dirty code to clean options dictionary as extracted by docopt.
def cleanOptions(options):
    cleanedOpts = {}
    for k,v in options.items():
        # Get rid of -- and <> from opts
        cleanedOpts[k.replace('--','').replace('<','').replace('>','')] = v

    return cleanedOpts

def doRsync(exposureSet, imageType, userId = 'xfer', remoteMachine = 'atlas-base-adm02.ifa.hawaii.edu', remoteLocation = '/atlas', localLocation = '/atlas', getMetadata = False, metadataExtension = '.tph'):

    exposureSet.sort()
    rsyncCmd = '/usr/bin/rsync'

    if imageType not in ['diff','red']:
        print("Image type must be diff or red")
        return 1

    imageExtension = {'diff':'.diff.fz','red':'.fits.fz'}

    rsyncFile = '/tmp/rsyncFiles_' + imageType + str(os.getpid()) + '.txt'

    # Create a diff and input rsync file
    rsf = open(rsyncFile, 'w')
    for exp in exposureSet:
        camera = exp[0:3]
        mjd = exp[3:8]

        imageName = camera + '/' + mjd + '/' + exp + imageExtension[imageType]

        if getMetadata:
            # We don't need the image, just get the metadata
            imageName = camera + '/' + mjd + '/' + exp + metadataExtension
            if metadataExtension == '.tph' and int(mjd) >= 57350:
                imageName = camera + '/' + mjd + '/' + 'AUX/' + exp + metadataExtension

        rsf.write('%s\n' % imageName)

    rsf.close()

    remote = userId + '@' + remoteMachine + ':' + remoteLocation + '/' + imageType
    local = localLocation + '/' + imageType

    # Get the diff images
    # 2018-04-16 KWS Removed the 'u' flag. We don't need to update the images.
    p = subprocess.Popen([rsyncCmd, '-axKL', '--files-from=%s' % rsyncFile, remote, local], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()

    if output.strip():
        print(output)
    if errors.strip():
        print(errors)

    return 0

