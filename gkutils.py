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
