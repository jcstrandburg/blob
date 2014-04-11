import pygame
from pygame.locals import *
from framework import GameController, Activity, EventListener
from managers import settings, resources
from animation import AnimatedSprite

class GoofBall(AnimatedSprite, EventListener):

    def __init__(self):
        AnimatedSprite.__init__(self)

        self.otherani = self.load_animation("otherani")        
        #self.baseani = self.load_animation("testani")
        self.anim_index = self.otherani

        #print self.baseani, self.otherani

        self.position = (10, 10)

    def update(self, timestep):
        AnimatedSprite.update(self, timestep)
        '''x, y = self.position
        x += timestep*10
        y += timestep*15
        self.position = (x, y)
        self.rect.center = self.position'''

    def get_anim_index(self):
        return self.anim_index

    def handle_event(self, event):
        if event.type == KEYUP:
            print "key up"
            if event.key == pygame.K_SPACE:
                print "jank"
                #self.anim_index = self.otherani
                print self.anim_index
                return 1
        return EventListener.handle_event(self,event)

class Anim2(AnimatedSprite):
       
    def __init__(self):
        AnimatedSprite.__init__(self)
        self.ani1 = self.load_animation("testani")
        self.rect.center = (200, 200)
    

class Listen1(EventListener):
    def handle_event(self, event):

        print "handle listen1"
        if event.type == KEYDOWN and event.key == pygame.K_a:
            print "a pressed in Listen1"
            return 1
        
        return EventListener.handle_event(self, event)

class ProtoActivity(Activity):

    def on_create(self, config):
        Activity.on_create(self, config)
        self.orlando = GoofBall()
        self.jimmy = Anim2()
        self.orgroup = pygame.sprite.RenderPlain(self.orlando)
        self.jimmies = pygame.sprite.RenderPlain(self.jimmy)
        self.timer = 0.0

        self.add_event_listener(Listen1(), (KEYUP, KEYDOWN))
        self.add_event_listener(self.orlando, (KEYUP, KEYDOWN))

    def update(self, timestep):
        Activity.update(self, timestep)
        self.orlando.update(timestep)
        self.jimmies.update(timestep)
        self.timer += timestep

    def handle_event(self, event):
        event_handled = 0
        
        if event.type == KEYUP:
            if event.key == pygame.K_ESCAPE:
                self.finish()
                event_handled = 1

        if not event_handled:
            Activity.handle_event(self, event)

    def draw(self, screen):
        Activity.draw(self, screen)
        self.orgroup.draw(screen)
        self.jimmies.draw(screen)

class TestAct(Activity):

    jimmies = []
    anim1 = None
    anim2 = None
    img1 = None
    img2 = None

    def on_create( self, config):
        #self.anim1 = resources.get( "otherani")
        #self.anim2 = resources.get( "testani")
        self.img1 = resources.get( "bbob")
        self.img2 = resources.get( "otherimage")

    def draw(self, screen):

        if self.anim1 is not None:
            screen.blit(self.anim1.get_frame(0), (0,0))
            screen.blit(self.anim1.get_frame(1), (30,0))
            screen.blit(self.anim1.get_frame(2), (60,0))
            screen.blit(self.anim1.get_frame(3), (90,0))
            screen.blit(self.anim1._imgsrc, (120,0))

        if self.anim2 is not None:
            screen.blit(self.anim2.get_frame(0), (0, 30))
            screen.blit(self.anim2.get_frame(1), (30,30))
            screen.blit(self.anim2.get_frame(2), (60,30))
            screen.blit(self.anim2.get_frame(3), (90,30))
            screen.blit(self.anim2._imgsrc, (120,30))

        screen.blit(self.img1, (10, 60))
        screen.blit(self.img2, (10, 90))

    def handle_event( self, event):
        if event.type == KEYDOWN:
            if event.key == pygame.K_a and self.anim1 is None:
                self.anim1 = resources.get( "otherani")
            elif event.key == pygame.K_s and self.anim2 is None:
                self.anim2 = resources.get( "testani")
            elif event.key == pygame.K_q:
                self.anim1 = None
            elif event.key == pygame.K_w:
                self.anim2 = None
            elif event.key == pygame.K_ESCAPE:
                self.finish()

        Activity.handle_event( self, event)


def main():
    gc = GameController()
    gc.startup()
    gc.start_activity(TestAct, None)
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


main()

