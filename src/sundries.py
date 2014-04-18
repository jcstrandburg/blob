
class GoofBall(AnimatedSprite, EventListener):

    def __init__(self):
        AnimatedSprite.__init__(self)

        self.otherani = self.load_animation("otherani")        
        self.baseani = self.load_animation("testani")
        self.anim_index = self.baseani
        self.position = (10, 10)

    def update(self, timestep):
        AnimatedSprite.update(self, timestep)
        x, y = self.position
        x += timestep*10
        y += timestep*15
        self.position = (x, y)
        self.rect.center = self.position

    def get_anim_index(self):
        return self.anim_index

    def handle_event(self, event):
        if event.type == KEYUP:
            if event.key == pygame.K_SPACE:
                self.anim_index = self.otherani
                return 1
        return EventListener.handle_event(self,event)

class TextWidget( pygame.sprite.Sprite, EventListener):

    def __init__(self, text):
        pygame.sprite.Sprite.__init__( self)
        self.text = text
        self.texts = []
        self.center = (100,100)
        
        font = pygame.font.Font(None, 36)
        self.texts.append( font.render(self.text, 1, (150, 150, 150), (50,50,50)))
        font = pygame.font.Font(None, 48)        
        self.texts.append( font.render(self.text, 1, (225, 225, 0), (50,50,50)))
        self.index = 0        
        self.select_text()
        
    def select_text( self):
        self.image = self.texts[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = self.center
        
    def update( self, timestep):
        pass

    def draw( self, screen):
        pass
        
    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.index = (self.index+1)%2
                self.select_text()
                return 1
        return EventListener.handle_event(self,event)        


class ScrollingBackground( object):

    def __init__(self, tag):
        #self.image = resources.get( tag)
        square = 500
        numstars = 500
        self.image = pygame.Surface( (square, square))
        for i in xrange( numstars):
            intensity = int(50+200*(float(i)/numstars))
            color = (intensity,intensity,intensity)
            x = random.randint( 0, square-1)
            y = random.randint( 0, square-1)
            self.image.set_at( (x, y), color)
        
        self.scrollx = 0.0
        self.scrolly = 0.0
        
    def update(self, timestep):
        self.scrollx -= timestep*150
        self.scrolly -= timestep*50
        
        if self.scrollx < -self.image.get_width():
            self.scrollx += self.image.get_width()
        if self.scrolly < -self.image.get_height():
            self.scrolly += self.image.get_height()
        
    def draw(self, screen):
    
        xrep = screen.get_width()/self.image.get_width() + 2
        count = 0
        for x in xrange( int(self.scrollx), screen.get_width(), self.image.get_width()):
            for y in xrange( int(self.scrolly), screen.get_height(), self.image.get_height()):
                screen.blit( self.image, (x, y))
                count += 1
                
        
class ProtoActivity(Activity):

    def on_create(self, config):
        Activity.on_create(self, config)
        self.orlando = GoofBall()
        self.orgroup = pygame.sprite.RenderPlain(self.orlando)

        self.add_event_listener(self.orlando, (KEYUP, KEYDOWN))

    def update(self, timestep):
        Activity.update(self, timestep)
        #self.orlando.update(timestep)
        self.orgroup.update( timestep)

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
                