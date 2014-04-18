import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
import os, sys


current_path = os.getcwd()
sys.path.insert(0, os.path.join( current_path, "src/pymunk-4.0.0" ) )

import pymunk as pm
import pymunk.pygame_util
from pymunk.vec2d import Vec2d


COLL_BALL = 1
COLL_SPINNER = 2
COLL_SEGMENT = 3
COLL_GUMBA = 4

class ProtoActivity(Activity):

    def addball(self):
        #if ( self.ball is not None):
        #    self.space.remove( self.ball, self.ball.body)

        mass = 10
        radius = 18
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
        ball = pymunk.Body( mass, inertia)
        ball.position = pygame.mouse.get_pos()[0], 700
        ball.friction = 1.0
        shape = pm.Circle( ball, radius, (0,0))
        shape.friction = 0.5
        shape.elasticity = 0.99
        shape.collision_type = COLL_BALL
        self.space.add( ball, shape)
        self.ball = ball

    def addgumba(self):
        gumba = pymunk.Body( pymunk.inf, pymunk.inf)
        gumba.position = (100,100)
        shape = pm.Circle( gumba, 25, (0,0))
        shape.color = (50,50,255)
        shape.elasticity = 0.01
        shape.collision_type = COLL_GUMBA
        self.space.add( gumba, shape)
        self.gumba = gumba
        gumba.velocity = Vec2d( 100,0)

    def spawnbox(self):
        pos = pygame.mouse.get_pos()
        pos = (pos[0], 750-pos[1])
        
        mass = 1
        size = 10
        points = [(-size,-size),(size,-size),(size,size),(-size,size)]
        inertia = pymunk.moment_for_poly(mass, points, (0,0))
        box = pymunk.Body( mass, inertia)
        box.position = pos
        shape = pymunk.Poly(box, points)
        shape.color = (0,255,0)
        shape.friction = 0.8
        shape.elasticity = 0.1
        self.space.add( box, shape)
        

    def on_create(self, config):
        Activity.on_create(self, config)
        self.space = pymunk.Space()
        self.space.gravity = 0,-900
        self.ball = None
        self.captured = False

        self.addgumba()


        line = pymunk.Segment( self.space.static_body, (0,0), (0,750), 5)
        line.collision_type = COLL_SPINNER
        self.space.add( line)

        body = pymunk.Body(pymunk.inf, pymunk.inf)
        body.position = Vec2d(600,600)
        circ = pymunk.Circle(self.space.static_body, 25, (600,600))
        circ.collision_type = COLL_SPINNER
        self.space.add( circ)
        
        #spinner thing
        body = pymunk.Body(pymunk.inf, pymunk.inf)
        body.position = (300,300)
        body.angle = math.pi/2
        lines = [pymunk.Segment(body, (0, 100), (0, -100), 5.0)]
        for l in lines:
            l.friction = 1.5
            l.elasticity = 1.5
            l.color = (0,255,0)
            #l.collision_type = COLL_SPINNER
        self.space.add( body, lines)
        self.spinner = body
        self.spinnerbody = lines[0]

        rot_body = pymunk.Body()
        rot_body.position = (300,300)

        rot_center = pm.PinJoint(body, rot_body, (0,0), (0,0))
        self.space.add( rot_center)

        floor = pymunk.Segment( self.space.static_body, (0,0), (750,0), 5.0)
        floor.friction = 1.0
        floor.elasticity = 0.2
        self.space.add( floor)
        self.space.add_collision_handler( COLL_BALL, COLL_BALL, begin=self.ball_ball_collide)
        self.space.add_collision_handler( COLL_BALL, COLL_GUMBA, begin=self.ball_gumba_collide)
        self.space.add_collision_handler( COLL_BALL, COLL_SPINNER, post_solve=self.ball_spinner_collide)
        


    def update(self, timestep):
        Activity.update(self, timestep)
        self.space.step( timestep)

        if self.gumba.position[0] > 700 and self.gumba.velocity[0] > 0:
            self.gumba.velocity[0] *= -1
        elif self.gumba.position[0] < 50 and self.gumba.velocity[1] < 0:
            self.gumba.velocity[0] *= -1

        #self.spinner.angular_velocity -= self.spinner.angular_velocity*timestep
        
        #self.space.step( 1.0/60)

    def ball_gumba_collide(self, space, arbiter):
        ball = arbiter.shapes[0]
        gumba = arbiter.shapes[1]
        if ball.body.velocity.get_length() > 10:
            self.space.remove( gumba.body, gumba)
        else:
            self.space.remove( ball.body, ball)

        return False

    def ball_ball_collide(self, space, arbiter):
        print "ookla"
        ball = arbiter.shapes[0]

        return True

    def stick_ball_to_spinner(self, bbody, sbody, pos, space):
        bbody.velocity = Vec2d(0,0)
        bbody.angular_velocity = 0
        bbody.group = 1
        pivot_joint = pymunk.PivotJoint(bbody, sbody, pos)
        pivot_joint.max_force = 50000.
        space.add(pivot_joint)
        
        phase = bbody.angle - sbody.angle 
        gear_joint = pymunk.GearJoint(bbody, sbody,phase,1)        
        gear_joint.max_force = 600000.
        space.add(gear_joint)
        print "done"

    def ball_spinner_collide(self, space, arbiter):
        ball, spinner = arbiter.shapes
        pos = arbiter.contacts[0].position
        ball.collision_type = 0
        space.add_post_step_callback(self.stick_ball_to_spinner, ball.body, spinner.body, pos, self.space)

        return True

    def handle_event(self, event):
        event_handled = 0
        
        if event.type == KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.finish()
                event_handled = 1
            elif event.key == pygame.K_SPACE:
                self.addball()
                event_handled = True
            elif event.key == pygame.K_p:
                self.addgumba()
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                mousepos = pygame.mouse.get_pos()
                mousepos = (mousepos[0],750-mousepos[1])

                shape = self.space.point_query_first( mousepos)
                if shape == self.spinnerbody:
                    self.captured = True
            elif event.button == 3:
                self.spawnbox()

        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.captured = False

        elif event.type == MOUSEMOTION:
            angledif = event.rel[0] + event.rel[1]
            #print angledif, event.rel
            if self.captured:
                mousedif = pygame.mouse.get_pos()
                mousedif = (mousedif[0], 750-mousedif[1])
                mousedif = (mousedif[0] - self.spinner.position[0], mousedif[1] - self.spinner.position[1])
                dist = math.sqrt( mousedif[0]*mousedif[0] + mousedif[1]*mousedif[1])
                angle = math.acos( mousedif[1]/dist)
                if mousedif[0] > 0:
                    angle = 2*math.pi-angle
                self.spinner.angle = angle


        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        pos = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (255,255,255), pos, 10)
        pymunk.pygame_util.draw( screen, self.space)

def main():
    gc = GameController()
    gc.startup()
    gc.start_activity(ProtoActivity, None)
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

