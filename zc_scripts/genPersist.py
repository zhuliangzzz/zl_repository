#!/bin/env python

"""Modules for joining Genesis 2000 scripting and the Python scripting language.

This module provides a persistency framework for the Genesis-Python interface.
Arbitrary Python objects may be stored directly into the Genesis job structure...placed
into a storage bucket, which ends up being the misc directory...

This arbitrary Python object can then be read back into memory during a later
session, thus providing a simple multi-session persistency model.  One of the storage
formats is XML, used if the bucket is instantiated as an instance of XmlBucket.
By default, the XmlBucket is used if gnosis.xml.pickle is installed.  You may choose
to modify that behaviour, however.

This model provides NO concurrency control, as it should generally not be needed.

Usage:
>>> job = genClasses.Job('test_job')
>>> job.open()
>>> myDict = {'thiskey': 22.354, 'thatkey': 16.402, 'otherkey': (1,0,0,3)}
>>> job.bucket.put(myDict, 'map_dict')


... days later ...


>>> job = genClasses.Job('test_job')
>>> job.open()
>>> myDict = job.bucket.get('map_dict')
>>> print myDict
{'thiskey': 22.354, 'thatkey': 16.402, 'otherkey': (1,0,0,3)}

NOTES: 
- Some special Python objects are not supported by this persistence model...specifically,
  genClasses.Job objects cannot be saved due to their special handling of __getattr__ calls.

- In order to use the XmlBucket class, the gnosis.xml modules must be installed.  You can get
  them from http://www.gnosis.cx/download/Gnosis_Utils-current.tar.gz and installed using distutils.
  (
    e.g. untar the stuff, cd to the directory and run 
    python setup.py build
    python setup.py install
  )



"""

__author__  = "Mike J. Hopkins"
__date__    = "18 August 2004"
__version__ = "$Revision: 1.4.1 $"
__credits__ = """ Guido ... and David Mertz for gnosis.xml.pickle"""


# Import standard Python modules
import os


#          Which persistency engine ?
#
# By default, we'll use XML if gnosis.xml.pickle is available.
# You may wish to hard-code a value for ENGINE, however.
#

import pickle as pickle
try:
    import gnosis.xml.pickle as xml_pickle
    ENGINE = 'XML'
except:
    print('Cannot import gnosis.xml, must use Bucket class.')
    ENGINE = 'cPickle'




#Identify yourself!
print("Using genPersist.py Rev " + __version__)

class Bucket:
    ''' The basic unit of persistency.  This class represents a storage bucket,
    which may have many objects stored within it.  Those objects may be of various
    types.
    '''
    
    def __init__(self, job):
        ''' Needs the genClasses.Job object instance passed in as a parameter '''
        self.job  = job
        self.dbloc = os.path.join(job.dbpath, 'misc')
        #self.user = os.path.join(job.dbpath, 'user')
        
    def _createFileName(self, name):
        ''' This method creates the name of the actual file which will be used to
        store the object in the Genesis job structure'''
        fname = os.path.join(self.dbloc, 'persist.'+name)
        return fname
    
    def _exists(self, fname):
        '''This (private) method checks to see if the filename already exists
        Returns 0 if not, 1 if it exists...'''
        if os.path.isfile(fname): return 1
        return 0
    
    def _dump(self, obj):
        ''' Private method to return a pickled string from the object (obj)'''
        obj_str = pickle.dumps(obj)
        return obj_str

    def _load(self, obj_str):
        ''' Private method to return an object out of a pickled string'''
        obj = pickle.loads(STR)
        return obj
        
    def exists(self, name):
        ''' This (public) method checks to see if the name already exists
        Returns 0 if not, 1 if it exists...'''
        fname = self._createFileName(name)
        return self._exists(fname)
        
    def put(self, obj, name, overwrite=0):
        ''' This method provides a way to place the object into the bucket
        usage: job.bucket.put(obj, 'cur_state')
        If the name already exists, and overwrite is set to 0 (default) then
        this method will return 1
        '''
        fname = self._createFileName(name)
        if self._exists(fname) and not overwrite: return 1
        obj_str = self._dump(obj)
        fo = open(fname, 'w')
        fo.write(obj_str)
        fo.close()
        return 0
        
    def get(self, name, raw=0):
        ''' This method gets an object out of the bucket 
        If the name does not exist, this method returns 1
        Optional raw parameter will return the data raw (e.g. pickled)'''
        fname = self._createFileName(name)
        if not self._exists(fname): return 1
        STR = open(fname, 'r').readlines()
        STR = ''.join(STR)
        if raw:    
            return STR
        else:
            return self._load(STR)


class XmlBucket(Bucket):
    ''' Subclass of Bucket, implementing xml.pickle instead of standard cPickle 
    This Class can only store Instance objects (e.g. classes).  
    If you want to store regular objects like dictionaries, just wrap them up as
    in an instance of the genClasses.Empty class :
        obj = genClasses.Empty()
        obj.dict = myPreviousDict
        job.bucket.put(obj, 'mydict')
    '''


    def __init__(self, job):
        Bucket.__init__(self, job)
        print('Creating XML Bucket Persistency Engine...')

    def _dump(self, obj):
        ''' This method overloads the _dump() method of the Bucket base class
        to provide an XML interface.'''
        xml_string = xml_pickle.XML_Pickler(obj).dumps()
        return xml_string

    def _load(self, obj_str):
        ''' This method overloads the _load() method of the Bucket base class 
        to provide an XML interface.'''
        obj = xml_pickle.XML_Pickler().loads(obj_str)
        return obj
        
            
        
if __name__ == '__main__':
    ''' Self-test code...'''

    dbpath = 'c:/tmp/job'
    
    class BogusJob:
        name = 'Test'
        def __init__(self):
            self.dbpath = dbpath
            self.bucket = Bucket(self)
            self.xmlbucket = XmlBucket(self)
    
    print('Creating directories...')
    if not os.path.isdir(dbpath): os.mkdir(dbpath)
    misc = os.path.join(dbpath, 'misc')
    if not os.path.isdir(misc): os.mkdir(misc)

    print('Creating Job...')
    job = BogusJob()
    
    print('Creating test data...')
    class MyClass: pass
        
    obj = MyClass()
    obj.a = ['mike', 'j', 'hopkins']
    obj.b = 23
    obj.c = {'aa': 98.77, 'rr': [5,6,7]}
    print(obj)
    



    print('\n'*2)
    # --------------------------------------------------
    print('Putting data...')
    job.bucket.put(obj, 'test_obj', overwrite=1)
    
    print('Getting RAW data...')
    STR = job.bucket.get('test_obj', raw=1)
    print(STR)
    
    print('Getting data...')
    newObj = job.bucket.get('test_obj')
    print(newObj)
    # --------------------------------------------------




    print('\n'*2)
    # --------------------------------------------------
    print('Putting data into XML...')
    job.xmlbucket.put(obj, 'xml_obj', overwrite=1)

    print('Getting RAW XML Data...')
    STR = job.xmlbucket.get('xml_obj', raw=1)
    print(STR)
    
    print('Getting data...')
    newObj = job.xmlbucket.get('xml_obj')
    print(newObj)
    # --------------------------------------------------

        
    
