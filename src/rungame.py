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
        print "insert tutorial here"

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
        self.junk = resources.get("testani").get_new_handle()

    def update( self, timestep):
        Activity.update( self, timestep)
        self.junk.cycle( timestep)

    def draw(self, screen):
        Activity.draw( self, screen)
        img = self.junk.get_current_frame()
        img2 = resources.get("animimage")
        pos = pygame.mouse.get_pos()
        screen.blit(img, pos)
        screen.blit(img2, (pos[0], pos[1]+50))


def main():
    gc = GameController()
    gc.startup()
    
    #gc.start_activity(GameplayActivity, {"level": gc.level_path(3)})
    #gc.start_activity(TestAct, {"level": gc.level_path(2)})
    #gc.start_activity(LevelSelectMenu, None)
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

