import pygame
import os

class AnimatedImage:

    _imgsrc = None
    _frame_lengths = []
    _frame_images = []

    def __init__( self, filepath):

        f = file( filepath)
        pathbase = os.path.split( filepath)[0]
        self._imgsrc = pygame.image.load( os.path.join( pathbase, f.readline().strip())).convert()
        self._numframes = int( f.readline())

        #split the image up into the individual frames
        frame_width = self._imgsrc.get_width()/self._numframes
        for i in xrange( 0, self._imgsrc.get_width(), frame_width):
            r = (i, 0, frame_width, self._imgsrc.get_height())
            self._frame_images.append( self._imgsrc.subsurface( r))

        #load the frame length intervals
        self._frame_lengths = f.readline().split()
        if len( self._frame_lengths) != self._numframes:
            raise Exception( "Frame count mismatch when loading animation "+filepath)
        for i in range( self._numframes):
            self._frame_lengths[i] = float( self._frame_lengths[i])

    def get_new_handle( self):
        return AnimationHandle( self._frame_images, self._frame_lengths)
        pass

        
class AnimationHandle:

    _frames = None
    _intervals = None
    _time = 0.0
    _cur_frame = 0
    _numframes =0

    def __init__( self, frames, intervals):
        self._numframes = len(frames)
        #if len( intervals) == len( frames):
        self._intervals = intervals
        self._frames = frames
        self._numframes = len( self._intervals)
        #else:
            #pass

    def cycle( self, time):
        self._time += time
        print "cycle"
        while self._time >= self._intervals[ self._cur_frame]:
            self._time -= self._intervals[ self._cur_frame]
            self._cur_frame = (self._cur_frame + 1)%self._numframes
            print "cycled to", self._cur_frame
            
    def reset( self):
        self._time = 0.0
        self._cur_frame = 0

    def get_current_frame( self):
        return self._frames[ self._cur_frame]

class AnimatedSprite(pygame.sprite.Sprite):

    _cur_animation = None
    _animations = []

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

    def load_animation( self, tag):
        next_index = len( self._animations)
        handle = resources.get( tag).get_new_handle()
        self._animations.append( handle)
        return next_index

    #this must be defined by the inheriting class
    def get_anim_index( self):
        pass

    def get_animation( self, index):
        return _animations[index]

    def update( self, timestep):
        index = self.get_anim_index()
        if index is not None:
            if index != self._cur_animation:
                self._cur_animation = index
                self._animations[ self._cur_animation].reset()
            self.image = self._animations[ self._cur_animation].get_image()

if __name__ == "__main__":
    
    anim = AnimatedImage( os.path.join( "res", "anim.ani"))      
    anim = anim.get_new_handle()
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
        
