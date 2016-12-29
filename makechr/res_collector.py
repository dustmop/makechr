import os
import glob
import sys
from py2exe.build_exe import py2exe as build_exe

class ResCollector(build_exe):
  def copy_extensions(self, extensions):
    build_exe.copy_extensions(self, extensions)
    source = os.path.join('makechr', 'res')
    target = os.path.join(self.collect_dir, source)
    if not os.path.exists(target):
      self.mkpath(target)
    for f in glob.glob(os.path.join(source, '*')):
      name = os.path.basename(f)
      self.copy_file(f, os.path.join(target, name))
      self.compiled_files.append(os.path.join(source, name))
