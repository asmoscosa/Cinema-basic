"""
py2app build script for MyApplication

Usage:
    python setup.py py2app
"""
from setuptools import setup
import sys
sys.path.insert(0, '/usr/local/Trolltech/Qt-4.8.5/lib/')
sys.path.insert(0, '/usr/local/lib/')
print sys.path

OPTIONS = {
  'argv_emulation':True
}

setup(
    app=["Cinema.py"],
    setup_requires=["py2app"],
)
