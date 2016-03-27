#! /usr/local/bin/python -uOO
#
# Usage: fit dir size
#
from __future__ import print_function
import copy, os, sys

class Fit:
  "Fit a set of files onto a disk"

  def __init__(self, Path, DiskSize):
    self.MAX      = DiskSize
    self.files    = {}
    self.disk     = {}
    self.cursize  = 0

    # fitting can take a long time so keep a copy of the best fit
    # in case the user ctrl-c's us and to make updates while running.
    self.curbest  = {}
    self.curwaste = self.MAX

    self.get_files(Path)

  def get_files(self, path):
    "fills the files dictionary with files from path and their sizes"
    total_size = 0
    for root, _, filenames in os.walk(path):
      for filename in filenames:
        fullname = os.path.join(root, filename)
        self.files[fullname] = os.path.getsize(fullname)
        total_size = total_size + self.files[fullname]
    if total_size <= self.MAX:
      raise ValueError("All files already fit.")

  def num_to_human(self, num):
    if num > 1024*1024:
      suffix = 'M'
      num = num / 1024 / 1024
    elif num > 1024:
      suffix = 'K'
      num = num / 1024
    else:
      suffix = 'B'
    if suffix == 'B':
      return "{:d}{:s}".format(int(num), suffix)
    return "{:.2f}{:s}".format(num, suffix)

  def statline(self, size, strend='\n'):
    wasted = self.MAX - size
    print("{:s}/{:s}               ".format(self.num_to_human(size),
      self.num_to_human(wasted)), end=strend)
    
  def print_disk(self, disk):
    "Print a disk"
    total_size = 0
    for name, size in disk.items():
      print(name) #, size)
      total_size = total_size + size
    self.statline(total_size)

  def fit(self):
    "Try to make an exact fit, selecting files from the filelist"

    # update progress when we have a better fit then previous
    if (self.MAX - self.cursize) < self.curwaste and self.cursize != self.MAX:
      self.curwaste = self.MAX - self.cursize
      self.curbest = copy.deepcopy(self.disk)
      self.statline(self.cursize, '\r')

    # if we have an exact fit we're done
    if self.cursize == self.MAX:
      print("==> Exact fit:")
      self.print_disk(self.disk)
      return True

    # otherwise, keep backtracking to make an exact fit
    else:
      for name, size in self.files.items():
        if not name in self.disk and self.cursize + size <= self.MAX:
          self.disk[name] = size
          self.cursize = self.cursize + size
          if self.fit():
            return True;
          del(self.disk[name])
          self.cursize = self.cursize - size
    return False

if __name__ == "__main__":
  optlen = len(sys.argv)
  if optlen != 3:
    print("usage: fit dir size_in_mb")
  else:
    sys.setrecursionlimit(10000) # default is 1000 and might be to low
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
    fit = Fit(sys.argv[1], size)
    try:
      if not fit.fit():
        print("==> no exact match, best fit was:")
        fit.print_disk(fit.curbest)
    except KeyboardInterrupt:
      print("==> Interrupted, best fit was:")
      fit.print_disk(fit.curbest)

