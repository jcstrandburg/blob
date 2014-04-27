import pygame
from pygame.locals import *

import math, random, os, sys

from framework import GameController, Activity, EventListener, resources
from gameplay import GameplayActivity
import menu

class MainMenuActivity(menu.MenuActivity):
    def __init__(self, controller):
        menu.MenuActivity.__init__(self, controller)
    
    def on_create(self, config):
        menu.MenuActivity.on_create(self, config)
        font = pygame.font.Font(None, 36)
    
        widget = menu.TextButtonWidget( "Select Level", font, (200, 100))
        widget.onclick = self.do_select_level
        self.add_widget( widget)    

        widget = menu.TextButtonWidget( "How To Play", font, (200, 200))
        widget.onclick = self.do_how_to_play
        self.add_widget( widget)    

        widget = menu.TextButtonWidget( "Adios", font, (200, 300))
        widget.onclick = self.finish
        self.add_widget( widget)    

    def do_select_level(self):
        self.controller.start_activity( LevelSelectMenu, None)

    def do_how_to_play(self):
        self.controller.start_activity( TutorialActivity, None)

    def update(self, timestep):
        menu.MenuActivity.update(self, timestep)
    
    def handle_event(self, event):
        event_handled = False
        
        if event.type == KEYUP:
            if event.key == pygame.K_a:
                print self._widgets

        if not event_handled:
            menu.MenuActivity.handle_event(self, event)
            
    def draw(self, screen):
        menu.MenuActivity.draw(self, screen)

class TutorialActivity(Activity):
    def __init__(self, controller):
        Activity.__init__(self, controller)
        self.script = [
            ("tutorial1", [
                    (["This is Bob","Bob is a blob"],(200,200)), 
                    (["Bob is on a magical quest", "for sparkly things"], (200,300))
                ]),
            ("tutorial2", [
                    (["These are sparkly things","Touch these to beat a level"],(200,200))
                ]),
            ("tutorial3", [
                    (["Hold the right mouse button","to charge Bob up"],(200,200)), 
                    (["Release RMB to launch Bob","towards the mouse"],(300,300)),
                    (["Once Bob is launched he cannot","launch again until he has collided","or interacted with some object"],(400,400))
                ]),
            ("tutorial4", [
                    (["These are platformas and spinners","They are made of differenct materiasl that have differnt properites"],(200,200))
                ]),
            ("tutorial5", [
                    (["You can manually rotate spinners","that have gears in the middle"],(200,200)),
                    (["Left click on them and move","the mouse to rotate them"],(200,200)),
                ]),
            ("tutorial6", [
                    (["These are gravity wells","They either push or pull you."],(200,200)),
                    (["While you are in a gravity well","you are not subject to normal gravity."],(200,200)),
                    (["use them to perform","sweet orbital maneuvers."],(200,200)),
                ]),
            ("tutorial7", [
                    (["These are forcefields and magnets","They do what you might expect"],(200,200)),
                ]),
            ("tutorial8", [
                    (["These are sheep", "Sheep are assholes", "Sheep murdered your whole family"],(200,200)),
                    (["If you hit sheep at high speeds", "they die. If you hit them", "at low speed you die"],(200,200)),
                    (["Kill the evil bastards before", "they kill you"],(200,200)),
                ]),
        ]
        self.panel = 0
        self.caption = 0
        
        self.update_tut()
        
    def handle_event(self, event):
        event_handled = False
        
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                self.caption += 1
                if self.caption >= len( self.script[self.panel][1]):
                    self.caption = 0
                    self.panel += 1
                    
                if self.panel >= len(self.script):
                    self.finish()
                    return None
                    
                self.update_tut()

            elif event.key == K_ESCAPE:
                self.finish()
       
        if not event_handled:
            Activity.handle_event( self, event)
    
    def draw(self, screen):
        Activity.draw(self, screen)
        screen.blit( self.img, (0,0))

    def draw_text(self, target, texts):

        renders = []
        height = 0
        width = 0
        font = pygame.font.Font(None, 30)
        for l in texts[0]:
            img = font.render( l, 1, (255,255,0))
            renders.append( img)
            if img.get_width() > width:
                width = img.get_width()
            height += img.get_height()
         
        font = pygame.font.Font(None, 15)
        img = font.render( "Press SPACE to continue", 1, (255,255,0))
        renders.append(img)
        if img.get_width() > width:
            width = img.get_width()
        height += img.get_height()        
        
        basey = texts[1][1] - height/2
        rect = pygame.Surface((width+20, height+20))
        rect.fill((0,0,40))
        rect.set_alpha( 150)
        pos = (texts[1][0] - rect.get_width()/2, texts[1][1] - rect.get_height()/2)
        target.blit( rect, pos)
        for r in renders:
            pos = (texts[1][0] - r.get_width()/2, basey)
            basey += r.get_height()
            target.blit( r, pos)
            
    def update_tut(self):
        self.img = pygame.Surface( (750,750), pygame.SRCALPHA)
        self.img = resources.get( self.script[self.panel][0]).copy()
        self.draw_text( self.img, self.script[self.panel][1][self.caption])
        
class LevelSelectMenu(menu.MenuActivity):
    def __init__(self, controller):
        menu.MenuActivity.__init__(self, controller)
    
    def on_create(self, config):
        menu.MenuActivity.on_create(self, config)
        font = pygame.font.Font(None, 36)
    
        levels = self.controller.get_level_list()
        for index, lev in enumerate( levels):
            widget = menu.TextButtonWidget( "Level "+str(lev), font, (200, 100+index*30))
            widget.onclick = self.make_level_callback( lev)
            self.add_widget( widget)    

        widget = menu.TextButtonWidget( "Adios", font, (200, 200+index*30))
        widget.onclick = self.adios
        self.add_widget( widget)

        #self.bg = config['bg']

    def make_level_callback(self, levelnum):
        def callback():
            self.start_level( levelnum)
        return callback
        
    def start_level(self, levelnum):
        self.controller.start_activity(GameplayActivity, {"level": self.controller.level_path(levelnum)})
        
    def adios(self):
        print "adios"
        self.finish()

    def update(self, timestep):
        menu.MenuActivity.update(self, timestep)
        #self.bg.update( timestep)        
    
    def handle_event(self, event):
        event_handled = False
        
        if event.type == KEYUP:
            if event.key == pygame.K_a:
                print self._widgets

        if not event_handled:
            menu.MenuActivity.handle_event(self, event)
            
    def draw(self, screen):
        #self.bg.draw( screen)
        menu.MenuActivity.draw(self, screen)

class TestAct(Activity):
    def __init__(self, controller):
        Activity.__init__(self, controller)

    def on_create(self, config):
        self.junk = resources.get("enemyani").get_new_handle()

    def update( self, timestep):
        Activity.update( self, timestep)
        self.junk.cycle( timestep)

    def draw(self, screen):
        Activity.draw( self, screen)
        
        x = random.randint( 80, 90)
        screen.fill( (x,x,x))
        
        img = self.junk.get_current_frame()
        pos = pygame.mouse.get_pos()
        img2 = pygame.transform.scale( img, (40, 40))
        screen.blit(img2, pos)


def main():
    gc = GameController()
    gc.startup()
    
    #gc.start_activity(LevelSelectMenu, None)
    gc.start_activity(MainMenuActivity, None)
    #gc.start_activity( TestAct, None)
    running = True
    while running:

        #process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            else:
                gc.handle_event(event)
        
        gc.update()
        if gc.activities_empty():
            break
        gc.draw()

    print "attempting gc.cleanup"
    gc.cleanup()

if __name__ == "__main__":
    main()

