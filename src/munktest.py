import pygame
import math
from pygame.locals import *
from framework import GameController, Activity, EventListener
import random
from gameplay import GameplayActivity
import os, sys

      
            
def main():
    gc = GameController()
    gc.startup()
    
    gc.start_activity(GameplayActivity, {"level": gc.level_path(1)})
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

