import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
import random
import os, sys

current_path = os.getcwd()
sys.path.insert(0, os.path.join( current_path, "src/pymunk-4.0.0" ) )

import pymunk
from pymunk.vec2d import Vec2d
import xml.etree.ElementTree as ET

MAXCHARGE = 9.0
CHARGERATE = 6.0
IMPULSEMOD = 1600
GRAVITY = -600


def get_attrib(attribs, key, default=None, convert=None):
    '''helper function for fetching attributes from xml elements'''
    try:
        x = attribs[key]            
    except KeyError:
        x = default

    if convert is not None:
        x = convert(x)
    return x

class GameplayActivity(Activity):

    def make_spinner(self, mode, pos, angle, speed, length, material=0):
        evalues = [0.2, 1.0, 0.2]
        fvalues = [1.5, 0.5, 0.1]
        colors =  [ (255,50,50), (50,255,50), (50,50,255)]

        if mode == "free":
            spinner = pymunk.Body(10000000.,100000.)
        else:
            spinner = pymunk.Body(pymunk.inf,pymunk.inf)
        spinner.position = pos
        spinner.angle = angle
        spinner.angular_velocity = speed

        if mode == "drag":
            spinner.draggable = True

        shape = pymunk.Segment(spinner, (0,length), (0,-length), 5)
        shape.elasticity = evalues[material]
        shape.friction = fvalues[material]
        shape.color = colors[material]
        spinner.shape = shape
        
        rot_body = pymunk.Body()
        rot_body.position = pos
        rot_joint = pymunk.PinJoint( spinner, rot_body, (0,0), (0,0))
        
        self.space.add( spinner, shape, rot_joint)
        return spinner
    
    def make_wall(self, v1, v2, material=0, size=3):
        evalues = [0.2, 1.0, 0.2]
        fvalues = [1.5, 0.5, 0.1]
        colors =  [ (255,50,50), (50,255,50), (50,50,255)]

        wall = pymunk.Segment( self.space.static_body, v1, v2, size)
        wall.elasticity = evalues[material]
        wall.friction = fvalues[material]
        wall.color = colors[material]

        self.space.add( wall)
        return wall
        
    def reposition_player(self, pos, vel=None):
        self.player.position = pos
        if vel is not None:
            self.player.velocity = vel

    def make_player(self, position):
        mass = 10
        radius = 14
        ball = pymunk.Body( mass, pymunk.inf)
        ball.position = position
        shape = pymunk.Circle(ball, radius)
        shape.color = (255,255,255)
        shape.elasticity = 0.8
        shape.friction = 0.5
        self.space.add(ball, shape)
        self.player = ball
        
    def make_crates(self):
        mass = 4
        size = 20
        for i in range(10):
            body = pymunk.Body( mass, pymunk.moment_for_box(mass,size*2,size*2))
            body.position = (100, 40+i*size*2)
            shape = pymunk.Poly(body, ((-size,-size),(size,-size),(size,size),(-size,size)))
            body.shape = shape
            shape.color = (0,255,0)
            shape.elasticity = 0.10
            shape.friction = 0.8
            self.space.add( body, shape)
        
    def make_gravball(self, pos, mode, size, wellsize):
        puller = pymunk.Body(pymunk.inf,pymunk.inf)
        puller.position = pos
        puller.size = size
        puller.strength = size*65000
        puller.wellsize = wellsize

        circ = pymunk.Circle( puller, size)
        circ.friction = 1.0

        if mode == "push":
            puller.strength *= -1
            circ.color = (255,130,0)
        else:
            circ.color = (170,0,200)

        self.space.add( circ)
        return puller

    def make_magnet(self, pos, size):
        body = pymunk.Body()
        circ = pymunk.Circle( body, size, pos)
        circ.color = (180,180,180)
        circ.elasticity=0.01
        self.space.add( circ)

    def reload_level(self):
 
        #reset junk
        self.space = pymunk.Space()
        self.space.gravity = 0, GRAVITY
        self.make_player( (100, 100))
    
        self.gravballs = []

        #create all of the elements
        for e in self.level_elements:
            if e.tag == "spinner":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                mode = get_attrib(e.attrib, "mode")
                speed = get_attrib(e.attrib, "speed", 0.0, float)
                angle = get_attrib(e.attrib, "angle", 0.0, float)
                length = get_attrib(e.attrib, "length", 60, float)
                mat = get_attrib(e.attrib, "material", None, int)
                self.make_spinner( mode, (x,y), angle, speed, length, mat)
            elif e.tag == "segment":
                x1 = get_attrib(e.attrib, "x1", None, float)
                x2 = get_attrib(e.attrib, "x2", None, float)
                y1 = get_attrib(e.attrib, "y1", None, float)
                y2 = get_attrib(e.attrib, "y2", None, float)
                mat = get_attrib(e.attrib, "material", 0, int)
                self.make_wall( (x1,y1), (x2,y2), mat)
            elif e.tag == "gravball":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                mode = get_attrib(e.attrib, "mode")
                size = get_attrib(e.attrib, "size", None, int)
                wellsize = get_attrib(e.attrib, "wellsize", None, int)
                self.gravballs.append( self.make_gravball( Vec2d(x,y), mode, size, wellsize))
            elif e.tag == "magnet":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                size = get_attrib(e.attrib, "size", None, int)
                self.make_magnet( (x,y), size)                
            elif e.tag == "enemy":
                print "enemy not implemented"
            elif e.tag == "player":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                self.reposition_player( (x,y), (0,0))
            elif e.tag == "victory":
                print "victory not implemented"
            else:
                print "unrecognized tag", e.tag
        
    def on_create(self, config):
        Activity.on_create(self, config)
        self.charging = False
        self.charge = 0
        
        filename = config["level"]
        self.level_elements = ET.parse( filename).getroot()

        self.reload_level()
        #gb = self.make_gravball()
        #self.gravballs.append( gb)

        
    def update(self, timestep):
        Activity.update(self, timestep)
        
        if self.charging:
            self.charge += CHARGERATE*timestep
            if self.charge > MAXCHARGE:
                self.charge = MAXCHARGE
        
        pressed = pygame.mouse.get_pressed()
        pos = pygame.mouse.get_pos()
        self.player.reset_forces()
        if pressed[2]:
            xdif = pos[0] - self.player.position[0]
            ydif = (750-pos[1]) - self.player.position[1]
            dist = math.sqrt( xdif*xdif + ydif*ydif)
            mag = (9500000*750)/(dist*dist+300)*timestep
            force = (mag*xdif/dist,mag*ydif/dist)
            self.player.apply_force( force)

        for puller in self.gravballs:
            xdif = puller.position[0] - self.player.position[0]
            ydif = puller.position[1] - self.player.position[1]
            dist = math.sqrt( xdif*xdif + ydif*ydif)
            if dist < puller.wellsize:
                
                mag = (puller.strength)/(dist+10)*timestep
                force = Vec2d(xdif, ydif).normalized()*mag
                print mag
                self.player.apply_impulse( force)
                '''mag = (10000000000.)/(dist*dist+550)*timestep
                force = Vec2d(mag*xdif/dist,mag*ydif/dist)
                force *= timestep
                print mag
                self.ball.apply_impulse( force)'''
            
            
        self.space.step( timestep)
            
    def handle_event(self, event):
        event_handled = False
        
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.charging = True

        if event.type == MOUSEBUTTONDOWN and event.button == 3:
            mousepos = pygame.mouse.get_pos()
            mousepos = (mousepos[0],750-mousepos[1])
            print mousepos
            shape = self.space.point_query_first( mousepos)
            if shape is not None:
                print shape
                print hasattr( shape.body, "draggable")
            


        elif event.type == MOUSEBUTTONUP and event.button == 1:            
            
            if self.charging:
                pos = pygame.mouse.get_pos()
                xdif = pos[0] - self.player.position[0]
                ydif = (750-pos[1]) - self.player.position[1]
                dist = math.sqrt( xdif*xdif + ydif*ydif)
                mag = IMPULSEMOD*self.charge
                force = (mag*xdif/dist,mag*ydif/dist)
                print mag, force, math.sqrt(self.charge)
                self.player.apply_impulse( force)
                self.charging = False
                self.charge = 0.0
                
        elif event.type == KEYDOWN:

            if event.key == K_SPACE:
                self.player.position = (300,300)
                self.player.velocity = Vec2d(0,0)
            elif event.key == K_q:
                print self.tilt
        
        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        pymunk.pygame_util.draw( screen, self.space)
        pos = pygame.mouse.get_pos()

        for puller in self.gravballs:
            pos = ( int(puller.position[0]), 750-int(puller.position[1]))
            pygame.draw.circle( screen, (255,255,0), pos, puller.wellsize, 1)
        
        pos = Vec2d( pygame.mouse.get_pos())
        ballpos = pymunk.pygame_util.to_pygame( self.player.position, screen)
        if self.charging:
            ratio = self.charge/MAXCHARGE
            mousevect = (pos-ballpos).normalized()
            finalpos = ballpos + mousevect*40
            
            r = int(ratio*100)
            for x in range(r,10,-3):
                pos = ballpos+mousevect*x
                pygame.draw.circle( screen, (255,255-x*2,0), pos.int_tuple, x/8)

