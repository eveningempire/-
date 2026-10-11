"""Dependency probe invoked as a file to support Windows PowerShell 5.1."""
import sys

if sys.version_info[:2] != (3, 10):
    raise RuntimeError('PHM offline delivery requires Python 3.10')

import django
import daphne
import channels
import redis
import pywt
import yaml
import numpy
import pandas
import scipy
import sklearn
import torch
import torch_geometric

print('PHM Python runtime OK')
