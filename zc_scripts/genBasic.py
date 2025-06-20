#!/bin/env python



"""Modules for joining Genesis 2000 scripting and the Python scripting language.

This module provides VERY basic interface for the Genesis 2000 Environment.
It defines basic functions to allow COM, PAUSE, etc to be executed.

Usage would be like this:

from genBasic import *
COM('open_job,job='+jobName)
PAUSE('Job is opened')

"""

__author__  = "Mike J. Hopkins"
__date__    = "18 August 2004"
__version__ = "$Revision: 1.4.1 $"
__credits__ = """ Mike J. Hopkins for the code, Travis Smith for the idea"""

# NEED: genClasses.py
    
# Import Standard Python Modules
#import os, sys, string, time, re, math

# import package specific stuff
from genClasses import Genesis

#Identify
print("Using genBasic.py Rev " + __version__)


# Basic Genesis LMC wrapper functions.
def COM(args):
    '''Wrapper function for Genesis COM LMC
    args is string argument of COM command
    Returns a tuple of (gen.STATUS, gen.READANS, gen.COMANS)'''
    gen = Genesis()
    gen.COM(args)
    return (gen.STATUS, gen.READANS, gen.COMANS)

def PAUSE(msg):
    '''Wrapper function for Genesis PAUSE LMC
    args is string argument of PAUSE command
    Returns a tuple of (gen.STATUS, gen.READANS, gen.PAUSEANS)'''
    gen = Genesis()
    gen.PAUSE(msg)
    return (gen.STATUS, gen.READANS, gen.PAUSEANS)

def AUX(args):
    '''Wrapper function for Genesis AUX LMC
    args is string argument of AUX command
    Returns a tuple of (gen.STATUS, gen.READANS, gen.COMANS)'''
    gen = Genesis()
    gen.AUX(args)
    return (gen.STATUS, gen.READANS, gen.COMANS)

def MOUSE(args, mode='p'):
    '''Wrapper function for Genesis MOUSE LMC
    args is string argument of MOUSE command
    mode is 'p' (default) or 'r'
    Returns a tuple of (gen.STATUS, gen.READANS, gen.MOUSEANS)'''
    gen = Genesis()
    gen.MOUSE(args, mode)
    return (gen.STATUS, gen.READANS, gen.MOUSEANS)

def SU_ON():
    '''Wrapper function for Genesis SU_ON LMC'''
    gen = Genesis()
    gen.SU_ON()

def SU_OFF():
    '''Wrapper function for Genesis SU_ON LMC'''
    gen = Genesis()
    gen.SU_ON()

def VON():
    '''Wrapper function for Genesis VON LMC'''
    gen = Genesis()
    gen.VON()

def VOF():
    '''Wrapper function for Genesis VOF LMC'''
    gen = Genesis()
    gen.VOF()

def INFO(args):
    '''Wrapper function for running COM info...
    args is string of arguments to the info command
    Returns a list of strings which are lines from the output file'''
    gen = Genesis()
    return gen.INFO(args)

def DO_INFO(args):
    '''Wrapper function for running COM info...
    args is string of arguments to the info command
    returns a dictionary with all the information in the 
    output file from the info command.  Each array of information is accessed by a key to the
    dictionary that is returned. LIMITATION: Any string resembling a number will be converted
    to a number.  This means that a layer with the name '1.' or '1' will be returned later as
    the float 1.0'''
    gen = Genesis()
    return gen.DO_INFO(args)

# Self-test code
if __name__ == '__main__':
    COM('open_job,job=test')
    PAUSE('Looks like its working')


