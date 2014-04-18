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

MAXCHARGE = 9.0
CHARGERATE = 6.0
IMPULSEMOD = 1600
GRAVITY = -600

class GameplayActivity(Activity):

    def make_spinner(self, pos):
        spinner = pymunk.Body(10000.,100000.)
        spinner.position = pos
        #shape = pymunk.Poly(spinner, ((-10,-80), (10,-80), (10,80), (-10,80)))
        shape = pymunk.Segment(spinner, (0,60), (0,-60), 5)
        shape.elasticity = 2.0
        shape.friction = 0.10
        shape.color = (0,255,0)
        spinner.shape = shape
        
        rot_body = pymunk.Body()
        rot_body.position = pos
        rot_joint = pymunk.PinJoint( spinner, rot_body, (0,0), (0,0))
        
        self.space.add( spinner, shape, rot_joint)
        return spinner
    
    def make_wall(self, v1, v2):
        wall = pymunk.Segment( self.space.static_body, v1, v2, 3)
        wall.elasticity = 0.200
        wall.friction = 2.0
        wall.color = (200,0,0)
        self.space.add( wall)
        return wall
        
    def make_ball(self):
        mass = 10
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, 25)
        ball = pymunk.Body( mass, 10000000.)
        ball.position = (300, 650)
        shape = pymunk.Circle(ball, radius)
        shape.color = (255,255,255)
        shape.elasticity = 1.0
        shape.friction = 0.5
        self.space.add(ball, shape)
        self.ball = ball

    def make_walls(self):
        walls = [pymunk.Segment(self.space.static_body, (10, 10), (10, 740), 3),
                pymunk.Segment(self.space.static_body, (10, 10), (740, 10), 3),
                pymunk.Segment(self.space.static_body, (740, 740), (10, 740), 3),
                pymunk.Segment(self.space.static_body, (740, 740), (740, 10), 3)]
        for w in walls:
            w.elasticity = .2
            w.friction = 2.0
            w.color = (255,0,0)
        walls[0].color = (0,255,0)
        walls[0].elasticity = 1.0
        self.space.add( walls)
        
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
        
    def make_gravball(self):
        self.puller = pymunk.Body(pymunk.inf,pymunk.inf)
        self.puller.position = (500, 400)
        circ = pymunk.Circle( self.puller, 15)
        circ.friction = 1.0
        circ.body = self.puller
        self.space.add( circ)
        
    def on_create(self, config):
        Activity.on_create(self, config)
        self.charging = False
        self.charge = 0
                
        self.space = pymunk.Space()
        self.space.gravity = 0, GRAVITY
        
        self.make_walls()
        self.make_ball()
        self.spinner = self.make_spinner( (100,80))
        
        self.tilt = self.make_wall( (300, 100), (650, 140))
        self.make_wall( (150, 300), (450, 300))
        self.make_wall( (150, 500), (450, 500))
        
        self.make_gravball()

        
    def update(self, timestep):
        Activity.update(self, timestep)
        
        if self.charging:
            self.charge += CHARGERATE*timestep
            if self.charge > MAXCHARGE:
                self.charge = MAXCHARGE
        
        pressed = pygame.mouse.get_pressed()
        pos = pygame.mouse.get_pos()
        self.ball.reset_forces()
        if pressed[2]:
            xdif = pos[0] - self.ball.position[0]
            ydif = (750-pos[1]) - self.ball.position[1]
            dist = math.sqrt( xdif*xdif + ydif*ydif)
            mag = (9500000*750)/(dist*dist+300)*timestep
            force = (mag*xdif/dist,mag*ydif/dist)
            self.ball.apply_force( force)

        xdif = self.puller.position[0] - self.ball.position[0]
        ydif = self.puller.position[1] - self.ball.position[1]
        dist = math.sqrt( xdif*xdif + ydif*ydif)
        if dist < 150:
            
            mag = (1000000.)/(dist+10)*timestep
            force = Vec2d(xdif, ydif).normalized()*mag
            print mag
            self.ball.apply_impulse( force)
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

        elif event.type == MOUSEBUTTONUP and event.button == 1:            
            
            if self.charging:
                pos = pygame.mouse.get_pos()
                xdif = pos[0] - self.ball.position[0]
                ydif = (750-pos[1]) - self.ball.position[1]
                dist = math.sqrt( xdif*xdif + ydif*ydif)
                mag = IMPULSEMOD*self.charge
                force = (mag*xdif/dist,mag*ydif/dist)
                print mag, force, math.sqrt(self.charge)
                self.ball.apply_impulse( force)
                self.charging = False
                self.charge = 0.0
                
        elif event.type == KEYDOWN:

            if event.key == K_SPACE:
                self.ball.position = (300,300)
            elif event.key == K_q:
                print self.tilt
        
        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        pymunk.pygame_util.draw( screen, self.space)
        pos = pygame.mouse.get_pos()
        pos = ( int(self.puller.position[0]), 750-int(self.puller.position[1]))
        pygame.draw.circle( screen, (255,255,0), pos, 150, 1)
        
        pos = Vec2d( pygame.mouse.get_pos())
        ballpos = pymunk.pygame_util.to_pygame( self.ball.position, screen)
        if self.charging:
            ratio = self.charge/MAXCHARGE
            mousevect = (pos-ballpos).normalized()
            finalpos = ballpos + mousevect*40
            
            r = int(ratio*100)
            for x in range(r,10,-3):
                pos = ballpos+mousevect*x
                pygame.draw.circle( screen, (255,255-x*2,0), pos.int_tuple, x/8)
        
        body = self.spinner
        seg = body.shape
        pv1 = pymunk.pygame_util.to_pygame( body.position + seg.a.rotated( body.angle), screen)
        pv2 = pymunk.pygame_util.to_pygame( body.position + seg.b.rotated( body.angle), screen)
        pygame.draw.circle(screen, (200,200,200), pv1, 10)
        pygame.draw.circle(screen, (200,200,200), pv2, 10)