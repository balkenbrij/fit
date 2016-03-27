#! /usr/local/bin/python -uOO
#
# Usage: fit dir size
#
from __future__ import print_function
import os, sys

def num_to_human(num):
  suffix = 'B'
  if num > 1024*1024:
    suffix = 'M'
    num = num / 1024.0 / 1024.0
  elif num > 1024:
    suffix = 'K'
    num = num / 1024.0
  if suffix == 'B':
    return "{:d}{:s}".format(int(num), suffix)
  return "{:.2f}{:s}".format(num, suffix)

class Bin:
  "A bin to collect files"

  def __init__(self, size):
    self.free     = size
    self.items    = 0
    self.contents = []

  def add(self, name, size):
    if size > self.free:
      raise ValueError("Can't fit {}({}) into {}".format(name, \
        num_to_human(size), num_to_human(self.free)))
    self.contents.append((name, size))
    self.free  = self.free - size
    self.items = self.items + 1


class Fit:
  "Fit a set of files onto a disk"

  def __init__(self, Path, Binsize):
    self.binsize = Binsize 
    self.nbins   = 0
    self.bins    = []
    self.files   = []

    self.getfiles(Path)
    self.fit()
    self.printbins()


  def getfiles(self, path):
    "Read all files and check if they are not too big"
    for root, _, filenames in os.walk(path):
      for filename in filenames:
        fullname = os.path.join(root, filename)
        size = os.path.getsize(fullname)
        if size > self.binsize:
          raise ValueError("Can't fit {}({}) into {}".format(fullname, \
            num_to_human(size), num_to_human(self.binsize)))
        self.files.append((fullname, size))
    # sort by size so large items come first (pop will take largest first)
    self.files.sort(cmp=lambda a, b: a[1] - b[1])

  def getbin(self, size):
    "Get a bin which can hold size or create a new one"
    bestbin = None
    bestfree = self.binsize + 1
    for bin in self.bins:
      if size <= bin.free and bin.free < bestfree:
        bestbin = bin
        bestfree = bin.free
    if bestbin:
      return bestbin

    # no fit, create a new bin
    self.bins.append(Bin(self.binsize))
    self.nbins = self.nbins + 1
    return self.bins[-1]

  def fit(self):
    "Fit all files into bins"
    while self.files:
      name, size = self.files.pop()
      self.getbin(size).add(name, size)

  def printbins(self):
    wasted = 0
    for bin in self.bins:
      for name, _ in bin.contents:
        print(name)
      print("==> {:.1f}% wasted ({:s})".format((float(bin.free) / \
        self.binsize) * 100.0, num_to_human(bin.free)))
      print()
      wasted = wasted + bin.free

    print("Total {} bins, {:.1f}% ({}) wasted".format(self.nbins, \
      float(wasted)/(self.nbins*self.binsize)*100.0, num_to_human(wasted)))

if __name__ == "__main__":
  optlen = len(sys.argv)
  if optlen != 3:
    print("usage: fit dir size_in_mb")
  else:
    sizearg = sys.argv[2]
    size = 0
    if sizearg.endswith('G') or sizearg.endswith('g'):
      size = int(sizearg[:-1]) * 1024 * 1024 * 1024
    elif sizearg.endswith('M') or sizearg.endswith('m'):
      size = int(sizearg[:-1]) * 1024 * 1024
    elif sizearg.endswith('K') or sizearg.endswith('k'):
      size = int(sizearg[:-1]) * 1024
    else:
      size = int(sizearg)

    Fit(sys.argv[1], size)
