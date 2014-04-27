import pygame
from pygame.locals import *
from framework import Activity


class MenuWidget(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self._on_click_callback = None
        self.selected = False
        self.onclick = None
        
    def is_selectable(self):
        return False
        
    def is_clickable(self):
        return False
        
    def select(self):
        if not self.selected:
            self.selected = True
            self.on_select()

    def on_select(self):
        pass
        
    def unselect(self):
        if self.selected:
            self.selected = False
            self.on_unselect()
            
    def on_unselect(self):
        pass
        
    def draw(self, screen):
        screen.blit(self.image, self.rect)
            
class TextWidget(MenuWidget):

    def __init__(self, text, font, center):
        MenuWidget.__init__(self)
        self.text = text
        
        self.images = []
        self.images.append( font.render( self.text, 1, (200, 200, 200)))
        self.images.append( font.render( self.text, 1, (250, 250, 50)))
        self.image = self.images[0]
        
        self.rect = self.image.get_rect()
        self.rect.center = center
        

class TextButtonWidget(TextWidget):
    
    def __init__(self, text, font, center):
        TextWidget.__init__(self, text, font, center)
        self._callback = None
    
    def is_selectable(self):
        return True
    
    def is_clickable(self):
        return True
        
    def on_select(self):
        self.image = self.images[1]
        pass
        
    def on_unselect(self):
        self.image = self.images[0]
        pass
        
class MenuActivity(Activity):

    def __init__(self, controller):
        Activity.__init__(self, controller)
        self._widgets = []
        self._selectedwidget = None

    def update( self, timestep):
        Activity.update( self, timestep)
        for x in self._widgets:
            x.update(timestep)
        
    def handle_event( self, event):
        event_handled = False
        if event.type == MOUSEMOTION:
            event_handled = True
            
            if self._selectedwidget is not None and not self._selectedwidget.rect.collidepoint( event.pos):
                self._selectedwidget.unselect()
                self._selectedwidget = None
            
            for x in self._widgets:
                if x.is_selectable() and x.rect.collidepoint(event.pos):
                    self._selectedwidget = x
                    self._selectedwidget.select()
                    break        
        elif event.type == MOUSEBUTTONDOWN:
            for x in self._widgets:
                if x.is_clickable() and x.rect.collidepoint(event.pos):
                    if x.onclick is not None:
                        event_handled = True
                        x.onclick()
                        break                        
        elif event.type == KEYDOWN:
        
            if event.key == K_UP:
                if self._selectedwidget is not None:
                    index = self._widgets.index( self._selectedwidget)-1
                                        
                    for i in xrange(len(self._widgets)-1):
                        index2 = (index-i)%len(self._widgets)
                        if self._widgets[index2].is_selectable():
                            print "changing selection"
                            self._selectedwidget.unselect()
                            self._selectedwidget = self._widgets[index2]
                            self._selectedwidget.select()
                            break
                else:
                    if len( self._widgets) > 0:
                        self._selectedwidget = self._widgets[0]
                        self._selectedwidget.select()            
            
            elif event.key == K_DOWN:
                if self._selectedwidget is not None:
                    index = self._widgets.index( self._selectedwidget)+1
                                        
                    for i in xrange(len(self._widgets)-1):
                        index2 = (index+i)%len(self._widgets)
                        if self._widgets[index2].is_selectable():
                            self._selectedwidget.unselect()
                            self._selectedwidget = self._widgets[index2]
                            self._selectedwidget.select()
                            break
                else:
                    if len( self._widgets) > 0:
                        self._selectedwidget = self._widgets[0]
                        self._selectedwidget.select()            
            
            elif event.key == K_SPACE:
                if self._selectedwidget is not None and self._selectedwidget.is_clickable:
                    if self._selectedwidget.onclick is not None:
                        self._selectedwidget.onclick()
                        
            elif event.key == K_ESCAPE:
                self.finish()
        
        if not event_handled:
            Activity.handle_event( self, event)
        
    def draw( self, screen):
        Activity.draw( self, screen)
        for x in self._widgets:
            x.draw( screen)
        
    def add_widget(self, widget):
        self._widgets.append( widget)
