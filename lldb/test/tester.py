#!/usr/bin/env python
# -*- coding: utf8 -*-

import math, os.path, re, sys, time, unittest

def setupSysPath():
  testPath = sys.path[0]
  rem = re.match("(^.*/)test$", testPath)
  if not rem:
    print "This script expects to reside in .../test."
    sys.exit(-1)
  lldbBasePath = rem.group(1)
  lldbDebugPythonPath = "build/Debug/LLDB.framework/Resources/Python"
  lldbReleasePythonPath = "build/Release/LLDB.framework/Resources/Python"
  lldbPythonPath = None
  if os.path.isfile(lldbDebugPythonPath + "/lldb.py"):
    lldbPythonPath = lldbDebugPythonPath
  if os.path.isfile(lldbReleasePythonPath + "/lldb.py"):
    lldbPythonPath = lldbReleasePythonPath
  if not lldbPythonPath:
    print "This script requires lldb.py to be in either " + lldbDebugPythonPath,
    print "or" + lldbReleasePythonPath
    sys.exit(-1)
  sys.path.append(lldbPythonPath)

def prettyTime(t):
  if t == 0.0:
    return "0s"
  if t < 0.000001:
    return ("%.3f" % (t * 1000000000.0)) + "ns"
  if t < 0.001:
    return ("%.3f" % (t * 1000000.0)) + "µs"
  if t < 1:
    return ("%.3f" % (t * 1000.0)) + "ms"
  return str(t) + "s"

class ExecutionTimes:
  @classmethod
  def executionTimes(cls):
    if cls.m_executionTimes == None:
      cls.m_executionTimes = ExecutionTimes()
      for i in range(100):
        cls.m_executionTimes.start()
        cls.m_executionTimes.end("null")
    return cls.m_executionTimes
  def __init__(self):
    self.m_times = dict()
  def start(self):
    self.m_start = time.time()
  def end(self, component):
    e = time.time()
    if component not in self.m_times:
      self.m_times[component] = list()
    self.m_times[component].append(e - self.m_start)
  def dumpStats(self):
    for key in self.m_times.keys():
      if len(self.m_times[key]):
        sampleMin = float('inf')
        sampleMax = float('-inf')
        sampleSum = 0.0
        sampleCount = 0.0
        for time in self.m_times[key]:
          if time > sampleMax:
            sampleMax = time
          if time < sampleMin:
            sampleMin = time
          sampleSum += time
          sampleCount += 1.0
        sampleMean = sampleSum / sampleCount
        sampleVariance = 0
        for time in self.m_times[key]:
          sampleVariance += (time - sampleMean) ** 2
        sampleVariance /= sampleCount
        sampleStandardDeviation = math.sqrt(sampleVariance)
        print key + ": [" + prettyTime(sampleMin) + ", " + prettyTime(sampleMax) + "] ",
        print "µ " + prettyTime(sampleMean) + ", σ " + prettyTime(sampleStandardDeviation)
  m_executionTimes = None

setupSysPath()

import lldb

class LLDBTestCase(unittest.TestCase):
  def setUp(self):
    lldb.SBDebugger.SetAsync(True)
    self.m_commandInterpreter = lldb.SBDebugger.GetCommandInterpreter()
    if not self.m_commandInterpreter:
      print "Couldn't get the command interpreter"
      sys.exit(-1)
  def runCommand(self, command, component):
    res = lldb.SBCommandReturnObject()
    ExecutionTimes.executionTimes().start()
    self.m_commandInterpreter.HandleCommand(command, res, False)
    ExecutionTimes.executionTimes().end(component)
    if res.Succeeded():
      return res.GetOutput()
    else:
      self.fail("Command " + command + " returned an error")
      return None

class SanityCheckTestCase(LLDBTestCase):
  def runTest(self):
    ret = self.runCommand("show arch", "show-arch")

suite = unittest.TestLoader().loadTestsFromTestCase(SanityCheckTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)
ExecutionTimes.executionTimes().dumpStats()
