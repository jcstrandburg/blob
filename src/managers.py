import os
import pygame

class ResourceManager(object):
    _resources = {} #dictionary of actual resource objects, indexed by uri's
    _preloads = {} #dictionary of resource uri's and 
    _dirpath = None

    def __init__(self):
        pass

    def load( self, dirpath, listpath):
        self._dir = dirpath

        f = file( os.path.join( dirpath, listpath), 'r')
        for line in f:
            line = line.strip()
            if ( len( line) > 0 and line[0] != '#' ):
                restype, tag, path  = line.split( ',')
                restype, tag, path = restype.strip(), tag.strip(), path.strip()
                self._preloads[tag] = (restype, os.path.join( dirpath, path))

    '''def get( self, tag):
        try:
            return self._resources[tag]
        except KeyError:
            print "Resource", tag, "not loaded yet, attempting to load"
            try:
                preload = self._preloads[tag]
                if preload[0] == "image":
                    self._resources[tag] = pygame.image.load( os.path.join( self._dir, preload[1]))
                elif preload[0] == "sound":
                    self._resources[tag] = pygame.mixer.Sound( os.path.join( self._dir, preload[1]))
                else:
                    raise

                return self._resources[tag]

            except KeyError:
                print "Request for unkown resource", tag
                return None'''

    def get( self, tag):
        try:
            #get the uri
            restype, uri = self._preloads[tag]

            #try to grab it..
            try:
                return self._resources[ uri]

            #it's not loaded yet, try to load it
            except KeyError:

                if restype == "image":
                    self._resources[uri] = pygame.image.load( uri).convert()
                elif restype == "sound":
                    self._resources[uri] = pygame.mixer.Sound( uri)
                else:
                    raise Exception( "Unkown resource type "+restype+" on resource "+tag)                    
                    return None

                return self._resources[uri]

        except KeyError:
            raise Exception("Request for unkown resource " + tag)


class SettingsManager(object):

    _settings = {}
    def load( self, filepath):
        f = file( filepath, 'r')
        for line in f:
            line = line.strip()
            if ( len( line) > 0 and line[0] != '#' ):
                tag, string_value = line.split( '=')
                tag = tag.strip()
                string_value = string_value.strip()
                
                try:
                    value = int( string_value)
                except:
                    try:
                        value = float( string_value)
                    except:
                        value = string_value
                self.put( tag, value)

    def get( self, tag, default=None):
        try:
            return self._settings[tag]
        except KeyError:
            return default

    def put( self, tag, value):
        self._settings[tag] = value

    def dump( self):
        for key in self._settings:
            val = self._settings[key]
            print key, type( val), val

settings = SettingsManager()
resources = ResourceManager()
