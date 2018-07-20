import luigi
from buildMLDataSet import buildMLDataSet
from getATLASTrainingSetCutouts import getATLASTrainingSetCutouts

class GetCutOuts(luigi.Task):
    configFile = luigi.Parameter(default='~/config4_readonly.yaml') 
    mjds = luigi.ListParameter(default=[58226])
    stampSize = luigi.IntParameter(default=40)
    stampLocation = luigi.Parameter(default='/tmp/test')
    camera = luigi.Parameter(default='02a')
    downloadthreads=luigi.IntParameter(default=5)
    stampThreads = luigi.IntParameter(default=28)
    
    def requires(self):
        return []

    def output(self):
        return luigi.LocalTarget(self.stampLocation+'/good.txt') 

    def run(self):
        options = {'configFile':self.configFile,
            'mjds':self.mjds,
            'stampSize':self.stampSize,
            'stampLocation':self.stampLocation,
            'camera': self.camera,
            'downloadthreads': self.downloadthreads,
            'stampThreads': self.stampThreads}
             
        getATLASTrainingSetCutouts(options) 

class BuildMLDataSet(luigi.Task):
    good = luigi.Parameter()
    bad = luigi.Parameter()
    outputFile = luigi.Parameter()
    e = luigi.IntParameter(default=10)
    E = luigi.IntParameter(default=0)
    s = luigi.IntParameter(default=3)
    r = luigi.Parameter(default=None)
    N = luigi.Parameter(default='signPreserveNorm') 
    def requires(self):
        return [GetCutOuts()]

    def output(self):
        return luigi.LocalTarget(self.outputFile)

    def run(self):
        options = {
        'posFile':self.good,
        'negFile':self.bad,
        'outputFile':self.outputFile,
        'extent':self.e,
        'extension':self.E,
        'skewFactor':self.s,
        'rotate':self.r,
        'norm':self.N}
        buildMLDataSet(options)
       
if __name__ == '__main__':
    luigi.run()
