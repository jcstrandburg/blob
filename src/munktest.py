import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
import random
from gameplay import GameplayActivity
import os, sys
from managers import resources
import menu
from testbed import TestBed

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

def main():
    gc = GameController()
    gc.startup()
    
    #gc.start_activity(GameplayActivity, {"level": gc.level_path(3)})
    #gc.start_activity(TestAct, {"level": gc.level_path(2)})
    gc.start_activity(LevelSelectMenu, None)
    #gc.start_activity(TestBed, None)
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

    gc.cleanup()

if __name__ == "__main__":
    main()

