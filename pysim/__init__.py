"""
pysim - Python Wrapper for Simulink
"""

# Imports from standard library
from importlib.metadata import version

# Package metadata
__version__ = version(__name__)

# Populate package namespace
from pysim.pysim import Simulink, whereis_knee_jerk_model, plot
