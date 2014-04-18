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

MAXCHARGE = 16.0
CHARGERATE = 16.0
IMPULSEMOD = 500
GRAVITY = -600

GRAVBALL_COOLDOWN = -2.0
GRAVBALL_STREN = 180000

FORCEFIELD_STRENGTH = 1000.

COLL_PLAYER = 1
COLL_MAGNET = 2
COLL_SPINNER = 3
COLL_GRAVBALL = 4
COLL_SEGMENT = 5
COLL_FORCEFIELD = 6
COLL_VICTORY = 7


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
        shape.collision_type = COLL_SPINNER
        spinner.shape = shape
        
        rot_body = pymunk.Body()
        rot_body.position = pos
        rot_joint = pymunk.PinJoint( spinner, rot_body, (0,0), (0,0))
        
        self.space.add( spinner, shape, rot_joint)
        self.spinners.append( spinner)
        return spinner
    
    def make_victory(self, x, y, w, h):
        points = [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]
        vic = pymunk.Poly( self.space.static_body, points)
        vic.color = (255,255,0)
        vic.collision_type = COLL_VICTORY
        self.space.add( vic)
        self.victories.append(vic)
        return vic

    def make_forcefield(self, x, y, w, h, force):
        points = [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]
        
        field = pymunk.Poly( self.space.static_body, points)
        field.fieldforce = force
        field.collision_type = COLL_FORCEFIELD
        field.center = Vec2d( x+w/2, y+h/2)
        self.space.add( field)
        self.forcefields.append( field)


    def make_wall(self, v1, v2, material=0, size=3):
        evalues = [0.2, 1.0, 0.2]
        fvalues = [1.5, 0.5, 0.1]
        colors =  [ (255,50,50), (50,255,50), (50,50,255)]

        wall = pymunk.Segment( self.space.static_body, v1, v2, size)
        wall.elasticity = evalues[material]
        wall.friction = fvalues[material]
        wall.color = colors[material]
        wall.collision_type = COLL_SEGMENT

        self.space.add( wall)
        self.segments.append(wall)
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
        ball.joints = []

        shape = pymunk.Circle(ball, radius)
        shape.color = (255,255,255)
        shape.elasticity = 0.8
        shape.friction = 0.5
        shape.collision_type = COLL_PLAYER
        self.space.add(ball, shape)
        self.player = ball
        self.player.shape = shape

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
        puller.strength = size*GRAVBALL_STREN
        puller.wellsize = wellsize
        puller.timer = -.5

        circ = pymunk.Circle( puller, size)
        circ.friction = 1.0
        circ.collision_type = COLL_GRAVBALL
        puller.shape = circ

        if mode == "push":
            puller.strength *= -1
            circ.color = (255,130,0)
        else:
            circ.color = (170,0,200)

        self.space.add( circ)
        self.gravballs.append( puller)
        return puller

    def make_magnet(self, pos, size):
        body = pymunk.Body()
        circ = pymunk.Circle( body, size, pos)
        circ.color = (180,180,180)
        circ.elasticity=0.01
        circ.collision_type = COLL_MAGNET
        body.shape = circ
        self.space.add( circ)
        self.magnets.append( body)

    def reload_level(self):
 
        #reset junk
        self.space = pymunk.Space()
        self.space.gravity = 0, GRAVITY
        self.space.add_collision_handler( COLL_PLAYER, COLL_MAGNET, post_solve=self.player_magnet_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_GRAVBALL, post_solve=self.player_gravball_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_FORCEFIELD, pre_solve=self.player_forcefield_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_VICTORY, pre_solve=self.player_victory_collide)

        self.make_player( (100, 100))    
        self.gravballs = []
        self.spinners = []
        self.magnets = []
        self.segments = []
        self.enemies = []
        self.forcefields = []
        self.victories = []

        #create all of the elements
        for e in self.level_elements:
            print "loading", e.tag

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
                self.make_gravball( Vec2d(x,y), mode, size, wellsize)
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
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                w = get_attrib(e.attrib, "w", None, float)
                h = get_attrib(e.attrib, "h", None, float)
                self.make_victory( x, y, w, h)
            elif e.tag == "forcefield":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                w = get_attrib(e.attrib, "w", None, float)
                h = get_attrib(e.attrib, "h", None, float)
                fx = get_attrib(e.attrib, "forcex", None, float)
                fy = get_attrib(e.attrib, "forcey", None, float)
                self.make_forcefield( x, y, w, h, Vec2d(fx, fy))
        
            else:
                print "unrecognized tag", e.tag

    def stick_player_to_magnet(self, bbody, sbody, pos, space):
        bbody.velocity = Vec2d(0,0)
        bbody.angular_velocity = 0
        bbody.group = 1
        pivot_joint = pymunk.PivotJoint(bbody, sbody, pos)
        pivot_joint.max_force = 50000.
        space.add(pivot_joint)
        
        phase = bbody.angle - sbody.angle 
        gear_joint = pymunk.GearJoint(bbody, sbody,phase,1)        
        gear_joint.max_force = 600000.
        #space.add(gear_joint)

        bbody.joints = [pivot_joint]#, gear_joint]

        print "done"

    def player_magnet_collide(self, space, arbiter):
        player, spinner = arbiter.shapes
        pos = arbiter.contacts[0].position
        player.collision_type = 0
        space.add_post_step_callback(self.stick_player_to_magnet, player.body, spinner.body, pos, self.space)
        print "wat"

        return True

    def player_victory_collide(self, space, arbiter):
        print "you win fucker"
        return True

    def player_gravball_collide(self, space, arbiter):
        player, gravball = arbiter.shapes
        gravball.body.timer = GRAVBALL_COOLDOWN
        return True

    def player_forcefield_collide(self, space, arbiter):
        player, ff = arbiter.shapes
        #player.body.apply_impulse( ff.fieldforce)
        return False
        
    def on_create(self, config):
        Activity.on_create(self, config)
        self.charging = False
        self.charge = 0
        self.grabbed = None
        self.mousepos = Vec2d(0,0)
        
        self.filename = config["level"]
        self.level_elements = ET.parse( self.filename).getroot()
        self.reload_level()
        
    def update(self, timestep):
        Activity.update(self, timestep)

        pos = pygame.mouse.get_pos()
        self.mousepos = Vec2d( pos[0], 750-pos[1])
        
        if self.charging:
            self.charge += CHARGERATE*timestep
            if self.charge > MAXCHARGE:
                self.charge = MAXCHARGE

        if self.grabbed is not None:
            normvec = Vec2d(0,1)
            posvec = self.mousepos - self.grabbed.position
            angle = normvec.get_angle_between( posvec)
            if angle < 0:
                angle += math.pi*2
            self.grabbed.angle = angle

        for ff in self.forcefields:
            if ff.point_query( self.player.position):
                self.player.apply_impulse( ff.fieldforce*FORCEFIELD_STRENGTH*timestep)
            

        for puller in self.gravballs:

            if puller.timer > 0:

                diff = puller.position - self.player.position
                dist = diff.get_length()
                if dist < puller.wellsize:
                    
                    mag = (puller.strength)/(dist)*timestep
                    force = diff*mag/dist
                    self.player.apply_impulse( force)

            else:
                puller.timer += timestep
            
        self.space.step( timestep)
            
    def handle_event(self, event):
        event_handled = False
        
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            self.charging = True

        elif event.type == MOUSEBUTTONUP and event.button == 1:            
            
            if self.charging:
                pos = pygame.mouse.get_pos()
                xdif = pos[0] - self.player.position[0]
                ydif = (750-pos[1]) - self.player.position[1]
                dist = math.sqrt( xdif*xdif + ydif*ydif)
                mag = IMPULSEMOD*self.charge
                force = (mag*xdif/dist,mag*ydif/dist)
                print mag, force, math.sqrt(self.charge)
                for x in self.player.joints:
                    self.space.remove( x)
                self.player.shape.collision_type = COLL_PLAYER
                self.player.joints = []


                self.player.apply_impulse( force)
                self.charging = False
                self.charge = 0.0

        elif event.type == MOUSEBUTTONDOWN and event.button == 3:
            mousepos = pygame.mouse.get_pos()
            mousepos = (mousepos[0],750-mousepos[1])
            print mousepos
            shape = self.space.point_query_first( mousepos)
            if shape is not None:
                if hasattr( shape.body, "draggable") and shape.body.draggable:
                    self.grabbed = shape.body

        elif event.type == MOUSEBUTTONUP and event.button == 3:
            self.grabbed = None
                
        elif event.type == KEYDOWN:

            if event.key == K_SPACE:
                self.player.position = (300,300)
                self.player.velocity = Vec2d(0,0)
            elif event.key == K_ESCAPE:
                self.finish()
            elif event.key == K_q:
                self.level_elements = ET.parse( self.filename).getroot()
                self.reload_level()
        
        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        pymunk.pygame_util.draw( screen, self.space)
        pos = pygame.mouse.get_pos()

        for ff in self.forcefields:
            pygame.draw.line( screen, (255,255,255), pymunk.pygame_util.to_pygame( ff.center, screen), pymunk.pygame_util.to_pygame( ff.center+ff.fieldforce, screen))

        for puller in self.gravballs:
            if puller.timer > 0:
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

