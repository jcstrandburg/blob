'''
Justin Strandburg
CS 321
WWU Spring 2014
2D Pygame Project
Implementations of varius menu activities, and the main game loop
'''

import pygame
from pygame.locals import *

import math, random, os, sys

from framework import GameController, Activity, resources
from gameplay import GameplayActivity
import menu

class MainMenuActivity(menu.MenuActivity):
    def __init__(self, controller):
        menu.MenuActivity.__init__(self, controller)
    
    def on_create(self, config):
        menu.MenuActivity.on_create(self, config)
        font = pygame.font.Font(None, 36)
        bigfont = pygame.font.Font(None, 48)

        widget = menu.TextWidget( "Bob the Blob", bigfont, (375, 200))
        self.add_widget( widget)    

        widget = menu.TextButtonWidget( "Level Select", font, (375, 350))
        widget.onclick = self.do_select_level
        self.add_widget( widget)    

        widget = menu.TextButtonWidget( "How To Play", font, (375, 425))
        widget.onclick = self.do_how_to_play
        self.add_widget( widget)    

        widget = menu.TextButtonWidget( "Adios", font, (375, 550))
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
        screen.blit( resources.get("menubg"), (0,0))
        menu.MenuActivity.draw(self, screen)

class TutorialActivity(Activity):
    def __init__(self, controller):
        Activity.__init__(self, controller)
        self.script = [
            ("tut1a", [
                    (["This is Bob","Bob is a blob"],(225,250)), 
                    (["Bob is on a magical quest", "for sparkly things"], (225,425))
                ]),
            ("tut1b", [
                    (["Hold the right mouse button","to charge Bob up"],(300,250)), 
                    (["Release RMB to launch Bob","towards the mouse"],(350,250)),
                    (["Once Bob is launched he cannot","launch again until he has collided","or interacted with some object"],(400,450))
                ]),
            ("tut1c", [
                    (["These are sparkly things","Touch these to beat a level"],(550,250))
                ]),
            ("tut2a", [
                    (["These are platforms and spinners"],(400,350)),
                    (["They are made of different materials", "that have different properties"],(400,375)),
                ]),
            ("tut2b", [
                    (["You can manually rotate spinners","that have gears in the middle"],(200,400)),
                    (["Left click on them and move","the mouse to rotate them"],(300,575)),
                ]),
            ("tut3a", [
                    (["These are gravity wells","They either push or pull you."],(300,100)),
                    (["While you are in a gravity well","you are not subject to normal gravity."],(300,400)),
                ]),
            ("tut3b", [
                    (["Use them to perform","sweet orbital maneuvers."],(450,200)),
                ]),                
            ("tut4", [
                    (["These are forcefields and magnets","They do what you might expect"],(400,350)),
                ]),
            ("tut5a", [
                    (["These are sheep", "Sheep are assholes", "Sheep murdered your whole family"],(200,400)),
                    (["If you hit sheep at high speeds", "they die. If you hit them", "at low speed you die"],(350,400)),
                ]),
            ("tut5b", [
                    (["Kill the evil bastards", "before they kill you"],(500,600)),
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
        bigfont = pygame.font.Font(None, 48)
    
        widget = menu.TextWidget( "Select A Level:", bigfont, (375, 200))
        self.add_widget( widget)    

        levels = self.controller.get_level_list()
        width = int(math.ceil( math.sqrt( len(levels))))
        gridspacex = (750-200)/(width-1)
        gridspacey = (750-450)/(width-1)
        xbase = 100
        ybase = 225
        if int(math.ceil(float(len(levels))/width)) < width:
            ybase += gridspacey/2
        
        for index, lev in enumerate( levels):
            pos = (200, 100+index*30)
            pos = (xbase+gridspacex*(index%width), ybase+gridspacey*(index/width))

            widget = menu.TextButtonWidget( "Level "+str(lev), font, pos)
            widget.onclick = self.make_level_callback( lev)
            self.add_widget( widget)    

        widget = menu.TextButtonWidget( "Back", font, (375, 675))
        widget.onclick = self.adios
        self.add_widget( widget)

        #self.bg = config['bg']

    def make_level_callback(self, levelnum):
        def callback():
            self.start_level( levelnum)
        return callback
        
    def start_level(self, levelnum):
        self.controller.start_activity(GameplayActivity, {"level": levelnum})
        
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
        screen.blit( resources.get("menubg"), (0,0))
        menu.MenuActivity.draw(self, screen)

def main():
    gc = GameController()
    gc.startup()
    
    gc.start_activity(MainMenuActivity, None)
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

