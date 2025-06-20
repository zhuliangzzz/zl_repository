#!/bin/env python

"""Modules for joining Genesis 2000 scripting and the Python scripting language.

NEED: genClasses.py and genCommands.py

THIS MODULE *REQUIRES* ITSELF TO BE EMBEDDED IN CLASSES FROM THE genCommands.py 
and genClasses.py MODULES - IT WILL NOT WORK ON ITS OWN!!!

This module is used to define features.  It provides classes to represent Genesis
features.  Currently can represent Pad, Line, Arc, Text, and Barcode - no surface
support yet.  Slower, of course, than the DFM environment, but great for small jobs.
functionality over and above the basic Genesis commands. 

SEE parseFeatureInfo method in class Genesis, module genClasses
SEE featOut and featSelOut methods in class LayerCmds in genCommands"""

__author__  = "Mike J. Hopkins"
__date__    = "18 August 2004"
__version__ = "$Revision: 1.4.1 $"
__credits__ = """ Daniel R. Gowans, for contributions to content.
Frontline PCB, for an excellent scripting interface to Genesis 2000"""

# NEED: genClasses.py and genCommands.py

# Import Standard Python Modules
import os, sys, string, time, math

example_data = '''
### Layer - 01sp features data ###
#L 11.575 16.6562 11.5905 16.6408 r10 P 17 
#P 11.535 16.6328 r24 P 27 90 N
#P 11.655 16.6408 rect70x15 P 51 0 N;.smd
#S P 0
#OB 11.280000393701 16.525815551181 I
#OS 11.280000393701 16.698943996063
#OS 11.409846751969 16.698943996063
#OS 11.409846751969 16.525815551181
#OS 11.280000393701 16.525815551181
#OE

#A 11.2901844 16.7753242 11.4607668 16.6531159 11.3316995 16.6531159 r5.5 P 0 Y
#T 11.2850924 16.3908773 standard P 0 N 0.2 0.2 2.00000 'gg' 1;.nomenclature
B 11.1781601 16.3628712 UPC39 standard P 0 E 0.008 0.05 Y N Y Y T 'gg';.nomenclature
#T 11.2367183 16.678576 standard P 0 N 0.175 0.175 2.00000 'gg' 1;.nomenclature,.orbotech_plot_stamp
#T 11.2214422 16.5003555 canned_57 P 0 N 0.12 0.168 1.66667 'gg' 1;.nomenclature,.canned_text,.drill=non_plated
'''

#---------------------------------------------------------------------common routines

# USE THESE IF YOU WANT.  ALSO SEE parseFeatureInfo in genClasses.py, class Genesis
# --- Wrapper/Constructor Function ---
# gets passed the line from the info command
# returns the appropriate object.
def create(line):
	"""Part of the module - creates a class for the given line of the input file
		   line - line of text from output file"""
	 
	if not line[0] in ('#','B'): return 0
	shape = line[0]
	if line[0] == '#': shape = line[1]
	
	if shape == 'L':
		return Line(line)
	elif shape == 'P':
		return Pad(line)
	elif shape == 'A':
		return Arc(line)
	elif shape == 'T':
		return Text(line)
	elif shape == 'B':
		return Barcode(line)
	else:
		return 0

# --- Wrapper function to return a list of features --
# takes a list of lines as input.  
# Uses the output of INFO -t layer -e $JOB/$STEP/$lay -d FEATURES
def parse(lines):
	""" Part of the module - parses the lines from an input file and submits lines to create
	features.  Adds the features to a featureList.  Not used by any of the classes - not 
	necessary to use module"""
	
	fList = []
	for line in lines:
		if not len(line): continue
		if len(line) < 2: continue
		if line[1] == '#': continue
		feat = create(line)
		if feat:
			fList.append(feat)
	return fList
		

class Feature:
	"""This class defines an object which describes an individual feature.
	Gets passed in the line from the INFO command (-d FEATURES)"""
	
	def __init__(self, line):
		self.line   = string.strip(line)
		self.getAttrs()
	
	def getAttrs(self):
		"""Gets atributes of self by parsing the line passed
		leaves self.line intact except that everything after ';' is gone."""
		
		ss = string.splitfields(self.line, ';')
		self.line = ss[0]
		self.attributes = []
		self.values     = []
		self.attrs      = {}
		if len(ss) > 1:
			for attr in string.splitfields(ss[1], ','):
				if '=' in attr:
					name,val = string.splitfields(attr, '=')
				else:
					name,val = (attr, '1')
				
				# hack for "system" attributes
				if name[0] == '.':
					name = name[1:]
				self.attributes.append(name)
				self.values.append(val)
				self.attrs[name] = val
				STR = 'self.'+name+' = '+val
				try:
					exec('self.'+name+' = '+val)
				except:
					exec('self.'+name+' = '+`val`)
		
	def __repr__(self):
		STR = '<Feature.'+self.shape+' Object>'
		return STR
	
class Pad(Feature):
	"""This class defines an object which describes a Pad.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Pad (access by class.<var>)
			x, y - location
			symbol - Symbol used in drawing line
			polarity - Polarity of line
			dcode - dcode of symbol used
			rotation - rotation in degrees of Pad
			mirror - yes if mirrored"""
			
	def __init__(self, line):
		Feature.__init__(self, line)
		self.shape = 'Pad'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'Y/N':   {'Y': 'yes', 'N': 'no'},
			}
		self.parse()
		
	def parse(self):
		ss = string.split(self.line)
		if len(ss) < 8: return 0
		self.x        = string.atof(ss[1])
		self.y        = string.atof(ss[2])
		self.symbol   = ss[3]
		self.polarity = self.lookups['polarity'][ss[4]]
		self.dcode    = string.atoi(ss[5])
		self.rotation = string.atof(ss[6])
		self.mirror   = self.lookups['Y/N'][ss[7]]
		
class Line(Feature):
	"""This class defines an object which describes a Line.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Line (access by class.<var>)
			xs, ys, xe, ye - start and end points
			symbol - Symbol used in drawing line
			polarity - Polarity of line
			dcode - dcode of symbol used
			len - length of the line"""
		
	def __init__(self, line):
		Feature.__init__(self, line)
		self.shape = 'Line'
		self.lookups = {'polarity': {'P':'positive', 'N':'negative'}}
		self.parse()
		
	def parse(self):
		ss = string.split(self.line)
		if len(ss) < 8: return 0
		self.xs       = string.atof(ss[1])
		self.ys       = string.atof(ss[2])
		self.xe       = string.atof(ss[3])
		self.ye       = string.atof(ss[4])
		self.symbol   = ss[5]
		self.polarity = self.lookups['polarity'][ss[6]]
		self.dcode    = string.atoi(ss[7])
		# Calculate length of line
		self.len = math.hypot((float(self.xe)-float(self.xs)),(float(self.ye)-float(self.ys)))

class Arc(Feature):
	"""This class defines an object which describes an Arc.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Arc (access by class.<var>)
			xs, ys, xe, ye - start and end points
			xc, yc - center of arc
			symbol - Symbol used in drawing line
			polarity - Polarity of line
			dcode - dcode of symbol used
			direction - clockwise/counterclockwise"""
	def __init__(self, line):
		Feature.__init__(self, line)
		self.shape = 'Arc'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'direction': {'Y': 'CW', 'N': 'CCW'},
			}
		self.parse()
		
	def parse(self):
		ss = string.split(self.line)
		if len(ss) < 11: return 0
		self.xs       = string.atof(ss[1])
		self.ys       = string.atof(ss[2])
		self.xe       = string.atof(ss[3])
		self.ye       = string.atof(ss[4])
		self.xc       = string.atof(ss[5])
		self.yc       = string.atof(ss[6])
		self.symbol   = ss[7]
		self.polarity = self.lookups['polarity'][ss[8]]
		self.dcode    = string.atoi(ss[9])
		self.direction= self.lookups['direction'][ss[10]]

class Text(Feature):
	"""This class defines an object which describes a Text feature.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Text Feature (access by class.<var>)
			x, y - location
			font - font name
			polarity - Polarity of line
			rotation - rotation in degrees
			mirror - yes/no is it mirrored
			xsize - mils of letter in x direction
			ysize - mils of a letter in the y direction
			wfactor - scaling factor or width factor larger = thicker lines
			text - the text in the object
			version - not quite sure what the version means"""
			
	def __init__(self, line):
		Feature.__init__(self, line)
		self.shape = 'Text'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'Y/N':   {'Y': 'yes', 'N': 'no'},
			}
		self.parse()
		
	def parse(self):
		ss = string.split(self.line)
		if len(ss) < 12: return 0
		self.x        = string.atof(ss[1])
		self.y        = string.atof(ss[2])
		self.font     = ss[3]
		self.polarity = self.lookups['polarity'][ss[4]]
		self.rotation = string.atof(ss[5])
		self.mirror   = self.lookups['Y/N'][ss[6]]
		self.xsize    = string.atof(ss[7])
		self.ysize    = string.atof(ss[8])
		self.wfactor  = string.atof(ss[9])
		self.text     = ss[10]
		self.version  = string.atoi(ss[11])
		
class Barcode(Feature):
	"""This class defines an object which describes a Barcode.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Barcode Feature (access by class.<var>)
			x, y - location
			barcode - barcode type
			font - font name for under code
			polarity - Polarity of line
			rotation - rotation in degrees
			constant - Don't know
			width - mils of code in x direction
			heigt - mils of code in the y direction
			full_ascii - don't know
			cksum - checksum?
			invert_bg - invert the barcode yes/no
			add_text - add text to bottom of code yes/no
			text_loc - top/bot of the code
			text - text encoded in the barcode"""
			
	def __init__(self, line):
		Feature.__init__(self, line)
		self.shape = 'Barcode'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'boolean': {'Y':1,'N':0,  'yes':1,'no':0,  'y':1,'n':0,  '1':1,'0':0},
			'top/bot': {'T':'top','B':'bottom','top':'top','bot':'bottom'},
			}
		self.parse()
		
	def parse(self):
		ss = string.split(self.line)
		if len(ss) < 12: return 0
		self.x        = string.atof(ss[1])
		self.y        = string.atof(ss[2])
		self.barcode  = ss[3]
		self.font     = ss[4]
		self.polarity = self.lookups['polarity'][ss[5]]
		self.rotation = string.atof(ss[6])
		self.constant = ss[7]
		self.width    = string.atof(ss[8])
		self.height   = string.atof(ss[9])
		self.full_ascii  = self.lookups['boolean'][ss[10]]
		self.cksum       = self.lookups['boolean'][ss[11]]
		self.invert_bg   = self.lookups['boolean'][ss[12]]
		self.add_text    = self.lookups['boolean'][ss[13]]
		self.text_loc    = self.lookups['top/bot'][ss[14]]
		self.text        = ss[15]
