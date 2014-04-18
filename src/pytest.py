import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
from managers import settings, resources
from animation import AnimatedSprite
import random
import menu
import os, sys

current_path = os.getcwd()
sys.path.insert(0, os.path.join( current_path, "src/pymunk-4.0.0" ) )

import pymunk

class ScrollingBackground( object):

    def __init__(self):
        square = 500
        numstars = 500
        self.image = pygame.Surface( (square, square))
        for i in xrange( numstars):
            intensity = int(50+200*(float(i)/numstars))
            color = (intensity,intensity,intensity)
            x = random.randint( 0, square-1)
            y = random.randint( 0, square-1)
            self.image.set_at( (x, y), color)
        
        self.scrollx = 0.0
        self.scrolly = 0.0
        
    def update(self, timestep):
        self.scrollx -= timestep*150
        self.scrolly -= timestep*50
        
        if self.scrollx < -self.image.get_width():
            self.scrollx += self.image.get_width()
        if self.scrolly < -self.image.get_height():
            self.scrolly += self.image.get_height()
        
    def draw(self, screen):
    
        xrep = screen.get_width()/self.image.get_width() + 2
        count = 0
        for x in xrange( int(self.scrollx), screen.get_width(), self.image.get_width()):
            for y in xrange( int(self.scrolly), screen.get_height(), self.image.get_height()):
                screen.blit( self.image, (x, y))
                count += 1        
        
class MainMenuAct(menu.MenuActivity):
    def __init__(self, controller):
        menu.MenuActivity.__init__(self, controller)
        
    def on_create(self, config):
        menu.MenuActivity.on_create(self, config)
        font = pygame.font.Font(None, 36)
    
        widget = menu.TextButtonWidget( "Start", font, (200,100))
        widget.onclick = self.start
        self.add_widget( widget)
        
        widget = menu.TextButtonWidget( "Help", font, (200, 200))
        widget.onclick = self.help
        self.add_widget( widget)
        
        widget = menu.TextButtonWidget( "Config", font, (200, 300))
        widget.onclick = self.do_config
        self.add_widget( widget)
        
        widget = menu.TextButtonWidget( "Adios", font, (200, 400))
        widget.onclick = self.adios
        self.add_widget( widget)

        self.bg = config['bg']        
        
    def start(self):
        self.controller.start_activity( ProtoActivity, {"bg": self.bg})
        
    def help(self):
        print "help"
        
    def do_config(self):
        print "config"
        
    def adios(self):
        print "adios"
        self.finish()

    def update(self, timestep):
        menu.MenuActivity.update(self, timestep)
        self.bg.update( timestep)        
    
    def handle_event(self, event):
        event_handled = False
        
        if event.type == KEYUP:
            if event.key == pygame.K_a:
                print self._widgets

        if not event_handled:
            menu.MenuActivity.handle_event(self, event)
            
    def draw(self, screen):
        self.bg.draw( screen)
        menu.MenuActivity.draw(self, screen)

        
def cap(vector, mag):
    vmag = vector[0]*vector[0] + vector[1]*vector[1]
    vmag = math.sqrt( vmag)
    if vmag > mag:
        return (vector[0]*(mag/vmag),vector[1]*(mag/vmag))
    else:
        return vector

class ProtoActivity(Activity):

    def on_create(self, config):
        Activity.on_create(self, config)
        self.bob = Blob()
        self.bobgroup = pygame.sprite.RenderPlain( self.bob)
        self.map = Map( (750,750))
        self.map.init()
        self.charge = 0.0
        self.charging = False
        
    def update(self, timestep):
        Activity.update(self, timestep)
        self.bob.update(timestep)
        
        #post update
        ttype = self.map.get( (self.bob.rect.center[0]+self.bob.vel[0]*timestep, self.bob.rect.center[1]+self.bob.vel[1]*timestep))
        if ttype.block:
            self.bob.vel = [-self.bob.vel[0]*ttype.bounce,-self.bob.vel[1]*ttype.bounce]
            
        if self.charging:
            self.charge += timestep*3
            if self.charge > 3.0:
                self.charge = 3.0
            
    def handle_event(self, event):
        event_handled = False

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.charging = True
            self.charge = 0.0
        elif event.type == MOUSEBUTTONUP and event.button == 1:            
            vel = (event.pos[0]-self.bob.rect.center[0], event.pos[1]-self.bob.rect.center[1])
            vel = cap( vel, 300)
            print vel
            self.bob.vel = [self.bob.vel[0]+vel[0]*self.charge, self.bob.vel[1]+vel[1]*self.charge]
            self.charging = False
            self.charge = 0.0
            print "click"

        elif event.type == MOUSEBUTTONDOWN and event.button == 3:
            print "jeah"
            pos = event.pos
            xdif = pos[0]-self.bob.rect.center[0]
            ydif = pos[1]-self.bob.rect.center[1]
            dist = math.sqrt( xdif*xdif+ydif*ydif)
            mag = 200000./max( dist, 300)
            vel = (xdif*mag/dist, ydif*mag/dist)
            self.bob.vel[0] += vel[0]
            self.bob.vel[1] += vel[1]
        
        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        self.map.draw(screen)
        self.bobgroup.draw( screen)
        pygame.draw.line(screen, (255,255,255), pygame.mouse.get_pos(), self.bob.rect.center, 1)
        if self.charging:
            p = pygame.mouse.get_pos()
            pygame.draw.rect( screen, (255,255,255), (p[0], p[1],self.charge*10, 10))


class Blob(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface( (25,25))
        self.image.fill((255,0,255))
        self.image.set_colorkey((255,0,255))
        pygame.draw.circle( self.image, (0,255,0), (13,13), 12)
        self.rect = self.image.get_rect()
        self.rect.center = (100,100)
        self.vel = [0,0]
        
    def update(self, timestep):
        self.vel[1] += 250*timestep
        pos = self.rect.center
        pos = (pos[0] + self.vel[0]*timestep, pos[1] + self.vel[1]*timestep)
        self.rect.center = pos


class TileType(object):
    size=25

    def __init__(self, color=None, block=True, bounce=0.5, sticky=False):
        self.image = pygame.Surface( (TileType.size, TileType.size))
        if color is not None:
            self.image.fill( color)
        self.block = block
        self.bounce = bounce
        
        
class Map(object):
    def __init__(self, screensize):
        self.tiles = [[0 for y in xrange(0,screensize[0],TileType.size)] for x in xrange(0,screensize[1],TileType.size)]
        self.tileset = [TileType(None, False, 0.0), TileType((255,0,0), True, 0.5), TileType((0,0,255), True, .8)]
        pass
        
    def draw(self, screen):
        for y, row in enumerate( self.tiles):
            for (x, t) in enumerate( row):
                screen.blit(self.tileset[ self.tiles[y][x]].image, (x*TileType.size, y*TileType.size))
                
    def init(self):
        width = len(self.tiles[0])
        height = len(self.tiles)
    
        for t in xrange(width):
            self.tiles[0][t] = 1
            self.tiles[-1][t] = 1
            
        for t in xrange( 6, width-6):
            self.tiles[-7][t] = 2
            
        for t in xrange( 4, width-10):
            self.tiles[-14][t] = 2
            
        for t in xrange(height):
            self.tiles[t][0] = 1
            self.tiles[t][-1] = 1
            
    def get(self, pos):
        x = int(pos[0])/TileType.size
        y = int(pos[1])/TileType.size
        return self.tileset[ self.tiles[y][x]]

        
def main():
    gc = GameController()
    gc.startup()
    
    config = {"bg": ScrollingBackground()}    
    gc.start_activity(ProtoActivity, config)
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
    print "resources", len(resources._resources)

if __name__ == "__main__":
    main()

