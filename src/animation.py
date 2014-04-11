import pygame
import os
import managers

class AnimatedImage(object):

    _imgsrc = None
    _frame_lengths = []
    _frame_images = []

    def __init__(self, filepath):

        anifile = file(filepath)
        pathbase = os.path.split(filepath)[0]
        imgpath = anifile.readline().strip()
        self._imgsrc = pygame.image.load(os.path.join(pathbase, imgpath)).convert()
        self._numframes = int(anifile.readline())

        print "loading ani from", filepath
        print "loading image from", os.path.join(pathbase, imgpath)

        #split the image up into the individual frames
        frame_width = self._imgsrc.get_width()/self._numframes
        frame_height = self._imgsrc.get_height()
        for i in xrange(0, self._imgsrc.get_width(), frame_width):
            r = (i, 0, frame_width, frame_height)
            frame = pygame.Surface((frame_width, frame_height))
            frame.blit( self._imgsrc, (0,0), r)
            #frame = self._imgsrc.subsurface( r)
            self._frame_images.append( frame)
            
            #self._frame_images.append(self._imgsrc.subsurface(r).copy())

        #load the frame length intervals
        self._frame_lengths = anifile.readline().split()
        if len(self._frame_lengths) != self._numframes:
            raise Exception("Frame count mismatch when loading animation "+filepath)
        for i in range(self._numframes):
            self._frame_lengths[i] = float(self._frame_lengths[i])

    def get_new_handle(self):
        return AnimationHandle(self._frame_images, self._frame_lengths)

    def get_num_frames(self):
        return len( self._frame_images)

    def get_frame(self, index):
        return self._frame_images[index]


class AnimationHandle(object):

    _frames = None
    _intervals = None
    _time = 0.0
    _cur_frame = 0
    _numframes = 0

    def __init__(self, frames, intervals):
        self._numframes = len(frames)
        self._intervals = intervals
        self._frames = frames
        self._numframes = len(self._intervals)

    def cycle(self, time):
        self._time += time
        while self._time >= self._intervals[self._cur_frame]:
            self._time -= self._intervals[self._cur_frame]
            self._cur_frame = (self._cur_frame + 1)%self._numframes

    def reset(self):
        self._time = 0.0
        self._cur_frame = 0

    def get_current_frame(self):
        return self._frames[self._cur_frame]

class AnimatedSprite(pygame.sprite.Sprite):

    image = None
    rect = None
    _cur_animation = None
    _animations = []
    anim_index = 0

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

    def load_animation(self, tag):

        next_index = len(self._animations)
        handle = managers.resources.get(tag).get_new_handle()
        self._animations.append(handle)

        if self.image is None:
            self.image = handle.get_current_frame()
            self.rect = self.image.get_rect()

        return next_index

    #this must be defined by the inheriting class
    def get_anim_index(self):
        return self.anim_index

    def get_animation(self, index):
        return self._animations[index]

    def update(self, timestep):
        index = self.get_anim_index()
        #print index, self._cur_animation
        if index is not None:
            if index != self._cur_animation:
                print "changing animations"
                self._cur_animation = index
                self._animations[self._cur_animation].reset()
            self.image = self._animations[self._cur_animation].get_current_frame()
            self._animations[self._cur_animation].cycle(timestep)

if __name__ == "__main__":

    anim = AnimatedImage(os.path.join("res", "anim.ani"))      
    anim = anim.get_new_handle()
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
    anim.cycle(0.3)
        
