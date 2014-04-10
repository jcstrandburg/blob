import pygame
from pygame.locals import *
from framework import GameController, Activity, EventListener
from managers import settings, resources
from animation import Animation

'''class ChildActivity(Activity):

    iteration = 0

    def on_create( self, config):
        Activity.on_create( self, config)
        print "ChildActivity created"

    def on_resume( self):
        Activity.on_resume( self)
        print "ChildActivity resuming"

    def on_pause( self):
        Activity.on_pause( self)
        print "ChildActivity pausing"

    def on_destroy( self):
        Activity.on_destroy( self)
        print "ChildActivity destroying"

    def update( self, timestamp):
        Activity.update( self, timestamp)
        self.controller.start_activity( DoakesActivity, None)
        print "ChildActivity updating", self.iteration
        self.iteration += 1
        if self.iteration >= 2:
            self.finish()
'''

class GoofBall(pygame.sprite.Sprite):

    def __init__( self):
        pygame.sprite.Sprite.__init__(self)
        try:
            pass
        except pygame.error:
            print pygame.error
        
        self.image = resources.get( "bbob")
        self.rect = self.image.get_rect()
        self.position = (10, 10)

    def update( self, timestep):
        x, y = self.position
        x += timestep*50
        y += timestep*100
        self.position = (x, y)
        self.rect.center = self.position

class Listen1(EventListener):
    def handle_event( self, event):

        print "handle listen1"
        if event.type == KEYDOWN and event.key == pygame.K_a:
            print "a pressed in Listen1"
            return 1
        
        return EventListener.handle_event( self, event)

class Listen2(EventListener):
    def handle_event( self, event):

        print "handle listen2"
        if event.type == KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_s:
                print "a or s pressed in Listen2"
                return 1
        if event.type == KEYUP:
            if event.key == pygame.K_a:
                print "a released in Listen2"
                return 1
        
        return EventListener.handle_event( self, event)

class Listen3(EventListener):

    effect = None

    def __init__( self):
        EventListener.__init__( self)
        self.effect = resources.get( "snd2")

    def handle_event( self, event):

        print "handle listen3"
        if event.type == KEYUP:
            if event.key == pygame.K_d:
                print "d released in Listen3"
                return 1
        elif event.type == MOUSEBUTTONUP:
            print "Mouse button released in Listen3"
            return 1
        elif event.type == MOUSEBUTTONDOWN:
            print "Mouse button pressed in Listen3"
            self.effect.play()
            return 1
        
        return EventListener.handle_event( self, event)

    


    
class ProtoActivity(Activity):

    def on_create( self, config):
        Activity.on_create( self, config)
        self.orlando = GoofBall()
        self.orgroup = pygame.sprite.RenderPlain( self.orlando)
        self.timer = 0.0
        print "wat"

        self.add_event_listener( Listen1(), (KEYUP, KEYDOWN))
        self.add_event_listener( Listen2(), (KEYUP, KEYDOWN))
        self.add_event_listener( Listen3(), (MOUSEBUTTONUP, MOUSEBUTTONDOWN))

    def update( self, timestep):
        Activity.update( self, timestep)
        self.orlando.update( timestep)
        self.timer += timestep

        print timestep
        #print "timer:", self.timer
        #self.finish()

    def handle_event( self, event):
        event_handled = 0
        
        if event.type == KEYUP:
            if event.key == pygame.K_ESCAPE:
                self.finish()
                event_handled = 1

        if not event_handled:
            Activity.handle_event( self, event)

    def draw( self, screen):
        Activity.draw( self, screen)
        self.orgroup.draw( screen)

def main():
    gc = GameController()
    gc.startup()
    gc.start_activity( ProtoActivity, None)
    running = 1

    resources.get( "bbob2")

    while running:

        #process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = 0
            else:
                gc.handle_event( event)
        
        gc.update()
        if gc.activities_empty():
            break
        gc.draw()

    gc.cleanup()
    print "resources", len( gc.resources._resources)


main()

