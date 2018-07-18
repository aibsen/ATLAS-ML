import multiprocessing, queue, sys, os, time, datetime, logging

# 2013-07-31 KWS Allow overriding of number of processors (e.g. to use less than the CPU count)
def splitList(objectsForUpdate, bins = None):

   # Break the list of candidates up into the number of CPUs
   listLength = len(objectsForUpdate)

   if bins and bins <= 32:
      nProcessors = bins
   else:
      nProcessors = multiprocessing.cpu_count() 

   if listLength < nProcessors:
      nProcessors = listLength

   listChunks = []

   listChunkSize = int(round((listLength * 1.0) / nProcessors))

   i = 0
   if nProcessors > 1:
      for i in range(nProcessors-1):
         listChunks.append(objectsForUpdate[i*listChunkSize:i*listChunkSize+listChunkSize])

      # Append the last (probably uneven) chunk.  Might have 1 extra or 1 fewer members.
      listChunks.append(objectsForUpdate[(i+1)*listChunkSize:])
   else:
      listChunks.append(objectsForUpdate)

   return nProcessors, listChunks


# The problem here is that parallelProcess needs to know about the "worker" function
# and we don't want to be specific.  So pass the worker function as one of the parameters.

def parallelProcess(db, dateAndTime, nProcessors, listChunks, worker, miscParameters = [], firstPass = True, drainQueues = True):

   # Create a list of Queues.
   # 2017-05-30 KWS Don't create a queue if it doesn't need to be drained.
   if drainQueues:
      queues = []
      for i in range(nProcessors):
         q = multiprocessing.Queue()
         queues.append(q)

   # Start the cutting jobs.  Each job will add a list of objects to its own queue.
   jobs = []
   for i in range(nProcessors):
      if drainQueues:
         p = multiprocessing.Process(target=worker, args=(i,db, listChunks[i], dateAndTime, firstPass, miscParameters, queues[i]))
      else:
         p = multiprocessing.Process(target=worker, args=(i,db, listChunks[i], dateAndTime, firstPass, miscParameters))
      jobs.append(p)
      p.start()


   # EXPERIMENT - use get and WAIT - and join AFTER this is done (join code was previously here).

   print("Draining objects from the queue.")
   sys.stdout.flush()

   # EXPERIMENT - Pull just one large object off the queue rather than thousands of small ones
   #              This means we only ever need to grab one object off the queue.  Still don't know
   #              why we have to do this, but it seems to work consistently.

   fullListOfObjectForUpdate = []

   # 2013-08-06 KWS Sometimes our parallel processing doesn't require returning of any data
   if drainQueues:
      if nProcessors > 1:
         for i in range(nProcessors):
            print("Draining queue #%d" % i)
            sys.stdout.flush()
            fullListOfObjectForUpdate += queues[i].get()
            print("List Length = %d" % len(fullListOfObjectForUpdate))
      else:
         fullListOfObjectForUpdate = queues[0].get()
         print("List Length = %d" % len(fullListOfObjectForUpdate))


   # Wait for the jobs to complete AFTER the queues have been drained. If you try to do this
   # before draining the queue there is a danger of deadlocks.  This is a known queueing issue
   # to do with placing large objects on the queue.

   print("Waiting for jobs to complete...")
   sys.stdout.flush()

   for job in jobs:
      job.join()
      print("Job complete")
      sys.stdout.flush()

   return fullListOfObjectForUpdate

