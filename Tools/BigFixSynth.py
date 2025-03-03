# BigFixSynth - Synthetic data generator.
#
# 02/12/2025   MDL   Initial distro.
#
# TODO:
# 1. Better distribution for Crashes.
# 2. More parameterization and flexibility.  Feedback needed.

import argparse, sys
import matplotlib.pyplot as mp
import numpy             as np
import pandas            as pd

# Constants that control labels and the start date.
startDate    = '2025-01-01'
labelChaos   = 'Chaos'
labelCPU     = 'CPU %'
labelCrashes = 'Crashes'
labelIOPS    = 'IOPS'
labelIOQ     = 'IO Queue'
labelMemory  = 'Memory %'
labelPaging  = 'Paging %'

# Constants for various programmatic choices.
class choices:
   # The distributions to support.
   distributionBinomial   = 'binomial'
   distributionChiSquared = 'chisquared'
   distributionRandom     = 'random'
   # Output formats for the result. 
   outputCSV   = 'csv'
   outputGraph = 'graph'
   outputJSON  = 'json'
   outputTable = 'table'

# Min/max values for counters.
monitorMinMax = {labelCPU:     ( 2,    100),
                 labelCrashes: ( 0,      2),
                 labelIOPS:    (10, 100000),
                 labelIOQ:     ( 0,     30),
                 labelMemory:  ( 5,    100),
                 labelPaging:  ( 0,    100)} 

def generateTimeSeries(interval, samples):
   frequency = str(interval) + 's'
   dateRange = pd.date_range(startDate, freq=frequency, name='Timestamp', periods=samples)
   return(dateRange)

def generateChaos(timeSeries, chaosFactor, chaosProfile):
   # Iterate over the time series data and implement the chaos profile.
   samples = timeSeries.size
   chaosDetail = np.ones(samples)
   for ix in range(samples):
      if (chaosProfile == 'All'):
         chaosDetail[ix] = chaosFactor
      elif (chaosProfile == 'Monday9to10'):
         timeDetail = timeSeries[ix]
         if (timeDetail.day_of_week == 0):
            if ((timeDetail.hour >= 9) & (timeDetail.hour < 10)):
               chaosDetail[ix] = chaosFactor

   chaosFrame = {labelChaos: chaosDetail}
   return(chaosFrame)

def introduceChaos(chaosClass, monitorFrame, chaosFrame):
   # Iterate over the monitor [key,value] pairs and apply the chaos.
   chaosDetail = chaosFrame[labelChaos]
   for k, v in monitorFrame.items():
      if (k in chaosClass):
         # print(v)
         min = monitorMinMax[k][0]
         max = monitorMinMax[k][1]
         monitorFrame[k] = v * chaosDetail
         monitorIndex = monitorFrame[monitorFrame[k] <= min]
         monitorFrame.loc[monitorIndex.index.tolist(), k] = min
         monitorIndex = monitorFrame[monitorFrame[k] >= max]
         monitorFrame.loc[monitorIndex.index.tolist(), k] = max
   return(monitorFrame)

def generateMonitorDetail(label, rangeLow, rangeHigh, rangeMax, probability, samples, distribution):
   # Set up the random number generator.
   rng = np.random.default_rng()
   match distribution:
      case choices.distributionBinomial:
         monitorDetail = rng.binomial(n=rangeMax, p=probability,size=samples)
         monitorFrame = {label: monitorDetail}
      case choices.distributionRandom:
         monitorDetail = np.random.randint(rangeLow, rangeHigh + 1, size=samples)
         monitorFrame = {label: monitorDetail}
      case _:
         print("Unknown distribution.")
   return(monitorFrame)

def generateMonitor(interval, samples, distribution, chaosFrame):
   timeSeries = generateTimeSeries(interval, samples)
   dataMonitor = chaosFrame
   dataMonitor.update(generateMonitorDetail(labelCrashes,  0,   1,    1,  0.1, samples, distribution))
   dataMonitor.update(generateMonitorDetail(labelCPU,     10,  30,  100, 0.15, samples, distribution))
   dataMonitor.update(generateMonitorDetail(labelMemory,  60,  70,  100, 0.65, samples, distribution))
   dataMonitor.update(generateMonitorDetail(labelPaging,   3,   5,  100, 0.03, samples, distribution))
   dataMonitor.update(generateMonitorDetail(labelIOPS,   100, 900, 5000, 0.20, samples, distribution))
   dataMonitor.update(generateMonitorDetail(labelIOQ,      0,   3,   10, 0.05, samples, distribution))
   monitorFrame = pd.DataFrame(dataMonitor, index=timeSeries)
   return(monitorFrame)

def plotMonitor(outputFormat, monitorFrame):
   match outputFormat:
      case choices.outputCSV:
         monitorFrame.to_csv(sys.stdout)
      case choices.outputGraph:
         plot = monitorFrame.plot(title="BigFix Synthetic Data")
         mp.show() 
      case choices.outputJSON:
         monitorFrame.to_json(sys.stdout, date_format='iso', orient='index')
      case choices.outputTable:
         print(monitorFrame)
      case _:
         print("Unknown output format.")
   return()

def main(argv):
   # Parse the input. 
   parser = argparse.ArgumentParser(description="BigFix Synthetic Data Generator")
   parser.add_argument("--chaosFactor", "-f", required=False, dest="chaosFactor", type=float, default=1.0,
                                              help="The chaos factor aka monitor range multiplier.")
   parser.add_argument("--chaosClass",  "-c", required=False, dest="chaosClass",
                                              choices=[labelCrashes, labelCPU, labelMemory, labelPaging, labelIOPS, labelIOQ],
                                              type=str, default='CPU %', nargs="+",
                                              help="The monitor set to be affected by the chaos factor.")
   parser.add_argument("--chaosProfile","-p", required=False, dest="chaosProfile",
                                              choices=['All', 'Monday9to10'], type=str, default='Monday9to10',
                                              help="The time based profile for the chaos factor.")
   parser.add_argument("--distribution","-d", required=False, dest="distribution",
                                              choices=[choices.distributionRandom, choices.distributionBinomial], type=str,
                                              default=choices.distributionBinomial,
                                              help="The distribution to use for the generated data (default=" + choices.distributionBinomial + ").")
   parser.add_argument("--interval",    "-i", required=False, dest="interval", type=int, default=5,
                                              help="The sample time interval in seconds.")
   parser.add_argument("--samples",     "-s", required=False, dest="samples", type=int, default=12,
                                              help="The number of samples to generate.")
   parser.add_argument("--output",      "-o", required=False, dest="output",
                                              choices=[choices.outputGraph, choices.outputCSV, choices.outputJSON, choices.outputTable],
                                              type=str, default=choices.outputTable,
                                              help="The output format to display (default=" + choices.outputTable + ").")
   args = parser.parse_args()

   # Generate the dataframe and plot it.
   timeSeries   = generateTimeSeries(args.interval, args.samples)
   chaosFrame   = generateChaos(timeSeries, args.chaosFactor, args.chaosProfile)
   monitorFrame = generateMonitor(args.interval, args.samples, args.distribution, chaosFrame)
   monitorFrame = introduceChaos(args.chaosClass, monitorFrame, chaosFrame)
   plotMonitor(args.output, monitorFrame)

# The main processing loop.
if __name__ == "__main__":
   main(sys.argv[1:])
