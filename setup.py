import glob
import sys
from setuptools import setup

long_description = """Makechr is a tool for generating NES graphics from pixel art images. It creates the NES graphical components as separate files, letting you easily include these are binaries into homebrew ROMs. There are many options for handling different types of input images, check the README for more information."""

__version__ = '1.5'

if sys.argv[1] == 'py2exe':

  import py2exe
  import res_collector

  sys.path.append('makechr')

  DATA_FILES = [('res', glob.glob('makechr/res/*'))]
  OPTIONS = {'dll_excludes': ['MSVCP90.dll', 'w9xpopen.exe'],
             'bundle_files': 1,
             'compressed': True,
             }

  setup(name='Makechr',
        version=__version__,
        data_files=DATA_FILES,
        options={
          'py2exe': OPTIONS,
        },
        windows=[{
          'script': 'makechr/gui.py',
          'icon_resources': [(1, 'makechr/res/windows.ico')],
          'dest_base': 'makechr',
          'description': 'Makechr tool for generating NES graphics',
          'copyright': 'Copyright (C) 2019 Dustin Long',
        }],
        packages=['makechr'],
        zipfile=None,
        cmdclass={'py2exe': res_collector.ResCollector},
        install_requires=[
          'argparse',
          'Pillow',
          'protobuf',
          'watchdog',
          # wx
        ],
  )

else:

  setup(name='Makechr',
        version=__version__,
        description='Makechr tool for generating NES graphics',
        long_description=long_description,
        author='Dustin Long',
        author_email='me@dustmop.io',
        scripts=['bin/makechr'],
        url='http://dustmop.io/software/makechr',
        download_url=('https://github.com/dustmop/makechr/tarball/' +
                      __version__),
        license='GPL3',
        packages=['makechr', 'makechr.gen'],
        keywords='NES graphics gamedev',
        install_requires=[
          'argparse',
          'Pillow',
          'protobuf',
          'watchdog',
        ],
        package_data={'makechr': [p[8:] for p in glob.glob('makechr/res/*')]},
  )

