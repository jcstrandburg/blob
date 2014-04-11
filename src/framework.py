import pygame
import random
from managers import resources, settings
import time

class GameController(object):
    
    _activities = [] #stack of activities, only the top is currently active
    _pending = [] #list of activities waiting to be added to the stack
    _top_activity = None #the current active activity
    _time_stored = 0.0 #the amount of time that needs to be simulated in state changes
    _min_timestep = 0.0 #the lowest amount of time that can occur in a state update
    _max_timestep = 0.0 #the max time that can occure in a state update
    _max_steps = 0 #maximum number of state updates performed per frame drawn (for low fps situations)
    screen = None
    
    def __init__(self):
        pass

    def startup(self):

        settings.load('config.txt')
        resources.load(settings.get("res_dir", "res2"),
                             settings.get("res_list", "yermom"))

        w = settings.get("screenw", 400)
        h = settings.get("screenh", 400)
        self._min_timestep = settings.get("min_timestep", "0.005")
        self._max_timestep = settings.get("max_timestep", "0.1")
        self._max_steps = settings.get("max_steps_per_frame", 10)

        print self._min_timestep, self._max_timestep, self._max_steps

        self.screen = pygame.display.set_mode((w, h))
        pygame.mixer.init()

        self.clock = pygame.time.Clock()
        self.clock.tick()

    def cleanup(self):
        pass

    def draw(self):
        self.screen.fill((0,0,0) )
        top = self._top_activity()
        if top is not None:
            top.draw(self.screen)
        pygame.display.flip()

    def handle_event(self, event):
        top = self._top_activity()
        if top is not None:
            top.handle_event(event)

    def _top_activity(self):
        if len(self._activities) > 0:
            return self._activities[-1]
        else:
            return None

    def update(self, timestep = None):

        #add all pending activities to the stack
        if len(self._pending) > 0:

            #pause the top activity
            top = self._top_activity()
            if top is not None:
                top.pause()

            #add em
            for ActClass, config in self._pending:
                newact = ActClass(self)
                newact.on_create(config)
                self._activities.append(newact)

            #clear the list of pending activities
            del self._pending[:]

        #make sure we have activities to work with
        if self.activities_empty():
            return None

        #grab the top activity, then kill of this and any other finished activities
        top = self._top_activity()
        while top is not None and top.finished:
            top.pause()
            top.on_destroy()
            self._activities.pop()
            top = self._top_activity()

        #calculate the timestep if none provided
        if timestep is None:   
            ticks = self.clock.tick()
            timestep = float(ticks)/1000
            self._time_stored += timestep

        #force the top activity to resume and do an update
        if top is not None:
            top.resume()

            for i in range(self._max_steps):
                if self._time_stored > self._min_timestep:
                    timestep = min((self._time_stored, self._max_timestep))
                    top.update(timestep)
                    self._time_stored -= timestep
                
    #returns true if the activity stack is empty (does not check pending activities!)
    def activities_empty(self):
        return len(self._activities) == 0
        

    #add the given activity to a queue of pending adctivities to be added at the beginning of the next update
    def start_activity(self, ActClass, config):
        self._pending.append((ActClass, config))

    def _do_start_activity(self, ActClass, config):
        newact = ActClass(self)
        newact.on_create(config)
        self._activities.append(newact)
        if self._top_activity is not None:
            self._top_activity.pause()

class Activity(object):
    controller = None
    paused = 1
    finished = 0
    listeners = []

    def __init__(self, controller):
        self.controller = controller

    def on_create(self, config):
        pass

    def finish(self):
        self.finished = 1

    def on_destroy(self):
        pass

    def add_event_listener(self, listener, types):
        self.listeners.append((types, listener))

    def handle_event(self, event):
        for l in self.listeners:
            if event.type in l[0]:
                if l[1].handle_event(event):
                    break

    def resume(self):
        if self.paused:
            self.paused = 0
            self.on_resume()

    def on_resume(self):
        pass

    def draw(self, screen):
        pass

    def pause(self):
        if not self.paused:
            self.paused=1
            self.on_pause()

    def on_pause(self):
        pass

    def update(self, timestep):
        pass


class EventListener(object):

    def handle_event(self, event):
        return 0
