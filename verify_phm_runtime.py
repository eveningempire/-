"""Dependency probe invoked as a file to support Windows PowerShell 5.1."""
import sys

if not (3, 10) <= sys.version_info[:2] < (3, 13):
    raise RuntimeError('PHM requires Python 3.10, 3.11 or 3.12 (64-bit)')

import struct
if struct.calcsize('P') != 8:
    raise RuntimeError('PHM requires 64-bit Python')

import django
import daphne
import channels
import redis
import yaml
import corsheaders
import rest_framework
import channels_redis
import whitenoise
import openpyxl
import joblib
import numpy
import pandas
import scipy
import sklearn
import torch

print('PHM Python runtime OK')
