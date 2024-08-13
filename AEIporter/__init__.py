#!/usr/bin/env python

from . import AEIporter

__version__ = "2024.08.03"

def _open_aeiporter_gui():
    '''
    command-line interface
    '''
    AEIporter._runGui()
