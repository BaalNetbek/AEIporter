#!/usr/bin/env python

from . import AEIporter

__version__ = "0.0.1"

def _open_aeiporter_gui():
    '''
    command-line interface
    '''
    AEIporter._runGui()
