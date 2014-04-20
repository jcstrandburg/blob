import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
import random
from gameplay import GameplayActivity
import os, sys
from managers import resources

class PlatformRenderer(object):
    def __init__(self, images):
        self.images = images
        self.xslices = []
        for x in range(images[0].get_width()):
            self.xslices.append( images[0].subsurface( (x,0,1,images[0].get_height())))
        self.yslices = []
        for y in range(images[1].get_height()):
            self.yslices.append( images[1].subsurface( (0,y,images[0].get_width(),1)))
        
    def draw(self, screen, v1, v2):
    
        xdif = v2[0]-v1[0]
        ydif = v2[1]-v1[1]
    
        if math.fabs(xdif) > math.fabs(ydif):
            slope = float(ydif)/xdif
            if xdif < 0:
                v1, v2 = v2, v1
            for x in xrange( v2[0]-v1[0]):
                img = self.xslices[x%len(self.xslices)]
                screen.blit( img, (v1[0]+x, int(v1[1]+slope*x)-img.get_height()/2))
        else:
            slope = float(xdif)/ydif
            if ydif < 0:
                v1, v2 = v2, v1
            for y in xrange( v2[1]-v1[1]):
                img = self.yslices[y%len(self.yslices)]
                screen.blit( img, (int(v1[0]+slope*y-img.get_width()/2), v1[1]+y))

class TestAct(Activity):

    def on_create(self, config):
        print "yeah"
        self.images = []
        self.a = PlatformRenderer((pygame.image.load( "brick.png"), (pygame.image.load( "brick.png"))))
        self.b = PlatformRenderer((pygame.image.load( "ice.png"), (pygame.image.load( "icev.png"))))
        self.c = PlatformRenderer((pygame.image.load( "bounce.png"), (pygame.image.load( "bouncev.png"))))

        
    def draw(self, screen):
        Activity.draw(self, screen)

        img = resources.get("spinner1")
        
        screen.blit( img, (500,400))
        
        self.a.draw( screen, (100,60), (500,100))
        self.a.draw( screen, (600,60), (700,260))
        self.b.draw( screen, (80,300), (480,200))
        self.b.draw( screen, (700,300), (550,500))
        self.c.draw( screen, (100,500), (400,600))
        self.c.draw( screen, (400,500), (500,700))
            
def main():
    gc = GameController()
    gc.startup()
    
    gc.start_activity(GameplayActivity, {"level": gc.level_path(3)})
    #gc.start_activity(TestAct, {"level": gc.level_path(2)})
    running = 1
    while running:

        #process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = 0

            else:
                gc.handle_event(event)
        
        gc.update()
        if gc.activities_empty():
            break
        gc.draw()

    gc.cleanup()

if __name__ == "__main__":
    main()

