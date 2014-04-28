import math, random, os, sys
import xml.etree.ElementTree as ET
import pygame
from pygame.locals import *

from framework import GameController, Activity, EventListener, resources, settings

#import pymunk stuff
current_path = os.getcwd()
sys.path.insert(0, os.path.join( current_path, "src/pymunk-4.0.0" ) )
import pymunk, pymunk.pygame_util
from pymunk.vec2d import Vec2d

'''Constants go here'''
#player launch constants
LAUNCH_IND_LEN = 100
MAXCHARGE = 1.0
CHARGERATE = 1.0
IMPULSEMOD = 6500
GRAVITY = -600

PLAYER_IMPACT_TIME = 0.5

SPECIAL_GRAVITY = True

GRAVBALL_LIFE = 1.0
GRAVBALL_COOLDOWN = -0.25
GRAVBALL_STREN = 24000

FORCEFIELD_STRENGTH = 100.
STATUS_SCROLL_SPEED = 400
SPINNER_DAMPENING  = 0.15

#collision types
COLL_PLAYER = 1
COLL_MAGNET = 2
COLL_SPINNER = 3
COLL_GRAVBALL = 4
COLL_SEGMENT = 5
COLL_FORCEFIELD = 6
COLL_VICTORY = 7
COLL_ENEMY = 8
COLL_PARTICLE = 9

GAME_NORMAL = 0
GAME_OVER = 1
GAME_WON = 2
GAME_PAUSE = 3

LAYER_STATICS = 1
LAYER_DYNAMICS = 2
LAYER_FX_STATICS = 4
LAYER_FX_DYNAMICS = 8

PLAYER_PARTICLE_COLOR = (100,200,100)
ENEMY_PARTICLE_COLOR = (200,50,50)

PARTICLE_PHYSICS = True

extended_segment_render = False


def get_attrib(attribs, key, default=None, convert=None):
    '''helper function for fetching attributes from xml elements'''
    try:
        x = attribs[key]            
    except KeyError:
        x = default

    if convert is not None:
        x = convert(x)
    return x

class SegmentRenderer(object):
    extended_segment_render = True

    def __init__(self, image, size):
        self.image = image
        self.inflation = 4
        
    def draw( self, screen, seg):
        v1 = Vec2d( pymunk.pygame_util.to_pygame( seg.a, screen))
        v2 = Vec2d( pymunk.pygame_util.to_pygame( seg.b, screen))
        
        #extend the segments to match their collision box
        if self.extended_segment_render:
            vect = v2-v1
            vect /= vect.get_length()
            v2 += vect * seg.radius * .7
            v1 -= vect * seg.radius * .7
        
        xdif = v2[0]-v1[0]
        ydif = v2[1]-v1[1]
        slicesize = seg.radius*2 + self.inflation
    
        if math.fabs(xdif) > math.fabs(ydif):
            slope = float(ydif)/xdif
            if xdif < 0:
                v1, v2 = v2, v1
            for x in xrange( int(v2[0]-v1[0])):
                xpos, ypos = int(v1[0]+x), int(v1[1]+slope*x-slicesize/2)
                screen.blit( self.image, (xpos, ypos), (xpos,ypos,1,slicesize))
        else:
            slope = float(xdif)/ydif
            if ydif < 0:
                v1, v2 = v2, v1
            for y in xrange( int(v2[1]-v1[1])):
                xpos, ypos = int(v1[0]+slope*y-slicesize/2), int(v1[1]+y)
                screen.blit( self.image, (xpos, ypos), (xpos,ypos,slicesize,1))
    
class SpinnerRenderer(object):
    def __init__(self, image):
        self.image = image
        self.transforms = {}
        
    def draw(self, screen, rotation, scale, pos):
        try:
            scaled_rots = self.transforms[scale]
        except KeyError:
            scaled_rots = {}
            self.transforms[scale] = scaled_rots

        rotation = (int(rotation)/3)*3
        rotation = rotation%360

        try:
            img = scaled_rots[rotation]
        except KeyError:
            img = pygame.transform.rotozoom(self.image, rotation, scale)
            scaled_rots[rotation] = img

        pos = (pos[0]-img.get_width()/2, pos[1]-img.get_height()/2)
        screen.blit( img, pos)  
    
class GameplayActivity(Activity):
    
    def on_create(self, config):
        Activity.on_create(self, config)

        self.screen_size = pygame.display.get_surface().get_size()
        self.victory_anim = resources.get("goalani").get_new_handle()
        self.enemy_anim = resources.get("enemyani").get_new_handle()
        self.particle_limit = settings.get("particle_limit")
        self.particle_fps_limit = settings.get("particle_fps_limit")
        self.optimize_drawing = True
        
        self.segment_renderers = [
            SegmentRenderer(resources.get("woodtex"),11),
            SegmentRenderer(resources.get("oozetex"),11),            
            SegmentRenderer(resources.get("icetex"),11),
            SegmentRenderer(resources.get("voidtex"),11),
        ]
        self.spinner_renderers = [
            SpinnerRenderer(resources.get("spinner1")),
            SpinnerRenderer(resources.get("spinner2")),
            SpinnerRenderer(resources.get("spinner3")),
        ]
        
        self.levelnum = config["level"]
        self.filename = self.controller.level_path( config["level"])
        self.level_elements = ET.parse( self.filename).getroot()
        self.reload_level()
        
    def update(self, timestep):
        Activity.update(self, timestep)
 
        self.time += timestep
        pos = pygame.mouse.get_pos()
        self.mousepos = Vec2d( pos[0], 750-pos[1])
        pressed = pygame.mouse.get_pressed()
        self.update_status_text( timestep)
        self.victory_anim.cycle( timestep)
        self.enemy_anim.cycle( timestep)

        #deal with status text/images
        if self.status_offset < 0.0:
            self.status_offset += STATUS_SCROLL_SPEED*timestep
        
        #bail out now if the game is paused (or the player won)
        if self.game_mode == GAME_PAUSE or self.game_mode == GAME_WON:
            return None        
        
        #check for player off map
        if self.game_mode != GAME_OVER:
            pos = self.player.position
            if pos[0] < -200 or pos[1] < -200 or pos[0] > self.screen_size[0]+200 or pos[1] > self.screen_size[1]+200:
                self.kill_player()
        
        #enforce terminal velocity on player
        speed = self.player.velocity.get_length()
        self.max_speed = max(self.max_speed, speed)
        if speed > 1000.0:
            newspeed = (1-timestep)*1000.+timestep*speed
            self.player.velocity *= newspeed/speed
        
        if self.player_impact > 0.0:
            self.player_impact -= timestep
        
        #charge up the players launch speed
        if self.charging:
            self.charge_cap += CHARGERATE*timestep
            if self.charge_cap > MAXCHARGE:
                self.charge_cap = MAXCHARGE
            vec = self.mousepos - self.player.position
            if vec[0] > 0:
                self.player.facing = "right"
            else:
                self.player.facing = "left"
            self.charge = min(self.charge_cap, vec.get_length()/LAUNCH_IND_LEN)

        #handle dragging spinners
        if self.grabbed is not None:
            normvec = Vec2d(0,1)
            posvec = self.mousepos - self.grabbed.position
            self.drag_body.position = self.mousepos
            self.drag_body.velocity = 0, 0
            self.drag_body.reset_forces()

        for e in self.enemies:
            if (e.dir > 0 and e.position[0] > e.limits[1]) or (e.dir < 0 and e.position[0] < e.limits[0]):
                e.dir *= -1
            e.velocity = Vec2d( e.dir*100, e.velocity[1])
            
        #do forcefield updates
        for ff in self.forcefields:
            ff.imgoffset += ff.fieldforce*5*timestep
            if ff.point_query( self.player.position):
                self.player_launchable = True
                self.player.apply_impulse( ff.fieldforce*FORCEFIELD_STRENGTH*timestep*self.player.mass)
            
            if PARTICLE_PHYSICS:
                for p in self.particles:
                    if ff.point_query( p.position):
                        p.apply_impulse( ff.fieldforce*FORCEFIELD_STRENGTH*timestep*p.mass)

        #do particle decay
        #print len(self.particles)
        for p in self.particles:
            p.life -= timestep
            if p.life <= 0:
                self.space.remove( p, p.shape)
                self.particles.remove( p)

        
        for s in self.spinners:
            #force any draggable spinners to stop moving, reduces jitter and stuff
            if s.mode == "drag" and s != self.grabbed:
                s.angular_velocity = 0.0
                s.position = s.home_pos
                s.velocity = Vec2d(0,0)
            elif s.mode == "free":
                s.angular_velocity -= timestep*SPINNER_DAMPENING*s.angular_velocity
                

        #deal with gravity balls
        self.player_floating = False
        for g in self.gravballs:
            if g.shutdown:
                g.life += timestep
                if g.life > GRAVBALL_LIFE:
                    g.shutdown = False
                    g.life = GRAVBALL_LIFE            
                continue
        
            diff = g.position - self.player.position
            dist = diff.get_length()

            if dist < g.wellsize:
                g.life -= timestep
                if g.life < 0.0:
                    g.life = 0.0
                    g.shutdown = True

                d = max( math.pow(dist,1.25), 150)
                mag = (g.strength)/d*timestep
                force = self.player.mass*diff*mag/dist
                self.player.apply_impulse( force)
                self.player_launchable = True
                self.player_floating = True

            if PARTICLE_PHYSICS:
                for p in self.particles:
                    diff = p.position - g.position
                    dist = diff.get_length()
                    
                    if dist < g.wellsize:
                        d = max( math.pow(dist,1.25), 150)
                        mag = (g.strength)/d*timestep
                        force = p.mass*diff*mag/dist
                        p.apply_impulse( -force)
        
        #if the player is in a gravity well apply an impulse to cancel normal gravity
        if SPECIAL_GRAVITY and self.player_floating:
            self.player.apply_impulse( (0, self.player_float*timestep))

        self.space.step( timestep)
            
    def handle_event(self, event):
        event_handled = False
        
        if (event.type == MOUSEBUTTONDOWN and event.button == 3) or (event.type == KEYDOWN and event.key == K_TAB):
            if self.player_launchable:
                self.charging = True

        elif (event.type == MOUSEBUTTONUP and event.button == 3) or (event.type == KEYUP and event.key == K_TAB):
            
            if self.charging:
                #figure out the impulse vector
                diff = self.mousepos-self.player.position
                dist = diff.get_length()
                mag = IMPULSEMOD*self.charge
                force = diff * mag/dist

                #unstick the player from any sticky objects, re-enable collisions
                for x in self.player.joints:
                    self.space.remove( x)
                self.player.shape.collision_type = COLL_PLAYER
                self.player.joints = []

                #finish up
                self.make_particles( self.player.position, int(self.charge*20), PLAYER_PARTICLE_COLOR)
                self.player.apply_impulse( force)
                self.charging = False
                self.player_launchable = False
                self.charge = 0.0
                self.charge_cap = 0.0

        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
        
            #deal with draggable spinners
            mousepos = pygame.mouse.get_pos()
            mousepos = (mousepos[0],750-mousepos[1])
            shapes = self.space.point_query( mousepos)
            for shape in shapes:
                if hasattr( shape.body, "draggable") and shape.body.draggable:
                    self.grabbed = shape.body
                    mousebod = pymunk.Body()
                    mousebod.position = self.mousepos
                    joint = pymunk.PivotJoint(mousebod, shape.body, mousepos)
                    joint.max_force = 2e9
                    self.space.add(joint)
                    self.drag_joint = joint
                    self.drag_body = mousebod
                    break
                    

        elif event.type == MOUSEBUTTONUP and event.button == 1:

            #release the grabbed spinner
            if self.grabbed is not None:
                self.grabbed.velocity = Vec2d(0,0)
                self.grabbed.angular_velocity = 0.0
                self.grabbed.position = self.grabbed.home_pos
                self.grabbed.shape.position = self.grabbed.position
                self.grabbed.reset_forces()
                self.grabbed = None
            
            if self.drag_joint is not None:
                self.space.remove( self.drag_joint)
                self.drag_joint = None
                self.drag_body = None
                
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if self.game_mode != GAME_NORMAL:
                    self.finish()
                else:
                    self.pause_game()
            elif event.key == K_F2:
                self.complex_drawing = not self.complex_drawing
            elif event.key == K_SPACE:
                if self.game_mode == GAME_WON:
                    self.start_next_level()
                else:
                    self.resume_game()
            elif event.key == K_r:
                SegmentRenderer.extended_segment_render = not SegmentRenderer.extended_segment_render
                print SegmentRenderer.extended_segment_render
            elif event.key == K_q:
                self.level_elements = ET.parse( self.filename).getroot()
                self.reload_level()
            elif event.key == K_1:
                self.complex_drawing = not self.complex_drawing
            elif event.key == K_z:
                self.reposition_player( self.mousepos, (0,0))
            elif event.key == K_v:
                self.player_float += 100
                print self.player_float
            elif event.key == K_b:
                self.player_float -= 100
                print self.player_float
            elif event.key == K_p:
                self.make_particles( self.mousepos, 20, PLAYER_PARTICLE_COLOR)
            elif event.key == K_F12:
                resources.force_reload()
                print "schwat"
            elif event.key == K_d:
                self.optimize_drawing = not self.optimize_drawing
            elif event.key == K_F4:
                pygame.image.save(pygame.display.get_surface(), "screen.png")

        if not event_handled:
            Activity.handle_event(self, event)

    def draw_statics(self, screen):
        screen.blit(resources.get("background"), (0,0))    
    
        #draw platform segments
        for s in self.segments:
            self.segment_renderers[s.material].draw( screen, s)
            
        #draw magnets
        baseimg = resources.get("magnet")
        for m in self.magnets:
            pos = pymunk.pygame_util.to_pygame( m.position, screen)
            img = pygame.transform.smoothscale( baseimg, (int(m.shape.radius*2), (int(m.shape.radius*2))))
            offset = Vec2d(img.get_width()/2, img.get_height()/2)
            screen.blit( img, pos-offset)            
    
    def draw(self, screen):
        Activity.draw(self, screen)
       
        if not self.complex_drawing:
            pymunk.pygame_util.draw( screen, self.space)
            for ff in self.forcefields:
                pygame.draw.line( screen, (255,255,255), pymunk.pygame_util.to_pygame( ff.center, screen), pymunk.pygame_util.to_pygame( ff.center+ff.fieldforce, screen))
                
            #draw gravity balls
            wavesize = 25
            begin = int(0.5*self.time*wavesize)%wavesize
            for g in self.gravballs:
                if not g.shutdown:
                    pos = pymunk.pygame_util.to_pygame( g.position, screen)
                    if g.strength < 0:
                        for r in xrange(begin, g.wellsize, wavesize):
                            if r > 0:
                                pygame.draw.circle( screen, (200,60,0), pos, r, 1)
                    else:
                        for r in xrange(wavesize-begin, g.wellsize, wavesize):
                            if r > 0:
                                pygame.draw.circle( screen, (100,0,120), pos, r, 1)                

        else:
            if self.optimize_drawing:
                screen.blit( self.static_img, (0,0))
            else:
                self.draw_statics(screen)            
        
            #draw gravity balls
            wavesize = 25
            begin = int(0.5*self.time*wavesize)%wavesize
            for g in self.gravballs:
                if not g.shutdown:
                    pos = pymunk.pygame_util.to_pygame( g.position, screen)
                    if g.strength < 0:
                        for r in xrange(begin, g.wellsize, wavesize):
                            if r > 0:
                                pygame.draw.circle( screen, (200,60,0), pos, r, 1)
                    else:
                        for r in xrange(wavesize-begin, g.wellsize, wavesize):
                            if r > 0:
                                pygame.draw.circle( screen, (200,0,240), pos, r, 1)                
        
            #draw forcefields
            img = resources.get("fieldbg")
            for f in self.forcefields:
                imgw = img.get_width()
                imgh = img.get_height()
                offset = (int(f.imgoffset[0])%imgw, int(f.imgoffset[1])%imgh)
                topleft = pymunk.pygame_util.to_pygame(f.topleft, screen)
                sub = screen.subsurface( (topleft[0], topleft[1], f.dimensions[0], f.dimensions[1]))
                for x in xrange( -imgw, int(f.dimensions[0])+imgw, imgw):
                    for y in xrange( -imgh, int(f.dimensions[1])+imgh, imgh):
                        sub.blit( img, (x+offset[0], y-offset[1])) 

            #draw spinners
            conversion = 360/(2*math.pi)
            gear = resources.get("spingear")
            for s in self.spinners:
                pos = Vec2d( pymunk.pygame_util.to_pygame( s.position, screen))
                angle = s.angle
                angle = int(angle*conversion)
                material = s.material
                scale = s.length/60.0
                self.spinner_renderers[s.material].draw( screen, angle, scale, pos)
                if s.mode == "drag":
                    img = pygame.transform.rotate( gear, angle)
                    offset = Vec2d(img.get_width()/2, img.get_height()/2)
                    screen.blit( img, pos-offset)
            
            #draw particles
            for p in self.particles:
                pos = pymunk.pygame_util.to_pygame( p.position, screen)
                pygame.draw.circle(screen, p.color, pos, 2)
            
            #draw victory locations
            baseimg = self.victory_anim.get_current_frame()
            for v in self.victories:
                pos = pymunk.pygame_util.to_pygame( v.topleft, screen)
                img = pygame.transform.scale( baseimg, v.dimensions.int_tuple)
                screen.blit( img, pos)
                
            #draw enemies
            baseimg = self.enemy_anim.get_current_frame()
            flipped = pygame.transform.flip( baseimg, True, False)
            for e in self.enemies:
                pos = pymunk.pygame_util.to_pygame( e.position, screen)
                if e.velocity[0] < 0:
                    screen.blit( baseimg, (pos[0]-baseimg.get_width()/2, pos[1]-baseimg.get_height()/2))
                else:
                    screen.blit( flipped, (pos[0]-baseimg.get_width()/2, pos[1]-baseimg.get_height()/2))

            #draw the player
            if not self.player.dead:
                if self.charging:
                    baseimg = resources.get("player_charging")
                else:
                    if self.player_impact > 0:
                        baseimg = resources.get("player_impact")
                    else:
                        baseimg = resources.get("player")
                    
                if self.player.facing == "left":
                    img = pygame.transform.flip( baseimg, True, False)
                else:
                    img = baseimg
                    
                pos = pymunk.pygame_util.to_pygame( self.player.position, screen)
                offset = Vec2d( img.get_width()/2, img.get_height()/2)
                screen.blit( img, pos-offset)
        
        '''draw the launch indicator if the player is charging up'''
        mousepos = Vec2d( pygame.mouse.get_pos())#mouse position in screen coordinates
        playerpos = pymunk.pygame_util.to_pygame( self.player.position, screen)#player pos in screen coords
        if self.charging:
            ratio = self.charge/MAXCHARGE
            mousevect = (mousepos-playerpos).normalized()
            finalpos = playerpos + mousevect*40
            
            r = int(ratio*LAUNCH_IND_LEN)
            for x in range(r,10,-3):
                pos = playerpos+mousevect*x
                pygame.draw.circle( screen, (255,255-x*2,0), pos.int_tuple, x/8)
                
        if self.status_img is not None:
            screen.blit( self.status_img, (0,int(self.status_offset)))

    def clear_status_text(self):
        self.status_img = None
        self.status_offset = 0.0
        self.status_timer = 0.0
            
    def show_status_text(self, scroll, timer, lines):
        
        self.status_img = pygame.Surface( self.screen_size, pygame.SRCALPHA)
        self.status_timer = timer
        
        if not isinstance( lines[0], (list,tuple)):
            lines = [lines]
        
        renders = []
        height = 0
        width = 0
        for l in lines:
            font = pygame.font.Font(None, l[0])
            img = font.render( l[1], 1, (255,255,0))
            renders.append( img)
            if img.get_width() > width:
                width = img.get_width()
            height += img.get_height()
        
        basey = self.screen_size[1]/2 - height/2
        rect = pygame.Surface((width+20, height+20))
        rect.fill((0,0,40))
        rect.set_alpha( 150)
        self.status_img.blit( rect, (self.screen_size[0]/2 - rect.get_width()/2, self.screen_size[1]/2 - rect.get_height()/2))
        #pygame.draw.rect( self.status_img, (0,0,40), (self.screen_size[0]/2 - width/2, self.screen_size[1]/2 - height/2, width, height))        
        for r in renders:
            pos = (self.screen_size[0]/2 - r.get_width()/2, basey)
            basey += r.get_height()
            self.status_img.blit( r, pos)
            
        if scroll:
            self.status_offset = -(self.screen_size[1]+height)/2

    def  update_status_text(self, timestep):
    
        if self.status_timer < 0.0:
            return None
        
        elif self.status_timer < timestep:
            self.status_timer = 0.0
            self.status_offset = 0.0
            self.status_img = None

        else:
            self.status_timer -= timestep

    def make_wall(self, v1, v2, material=0, size=11):
        evalues = [0.12, 0.95, 0.12, 0.01]
        fvalues = [2.5, 0.5, 0.3, 2.0, 3.0]
        colors =  [ (255,50,50), (50,255,50), (50,50,255), (255,0,255)]

        wall = pymunk.Segment( self.space.static_body, v1, v2, size)
        wall.elasticity = evalues[material]
        wall.friction = fvalues[material]
        wall.color = colors[material]
        wall.collision_type = COLL_SEGMENT
        wall.material = material
        wall.layers = LAYER_FX_STATICS | LAYER_STATICS

        self.space.add( wall)
        self.segments.append(wall)
        return wall
        
    def make_spinner(self, mode, pos, angle, speed, length, material=0):
        evalues = [0.12, 1.1, 0.12]
        fvalues = [2.0, 0.5, 0.1]
        colors =  [ (255,50,50), (50,255,50), (50,50,255)]

        if mode == "free":
            mass = 1e2
            spinner = pymunk.Body(mass, pymunk.moment_for_segment( mass, (0,length), (0,-length)))
        elif mode == "drag":
            mass = 1e4
            spinner = pymunk.Body(mass, pymunk.moment_for_segment( mass, (0,length), (0,-length)))
        else:
            spinner = pymunk.Body(pymunk.inf,pymunk.inf)
        spinner.mode = mode
        spinner.position = pos
        spinner.home_pos = pos
        spinner.angle = angle
        spinner.angular_velocity = speed
        spinner.material = material
        spinner.length = length

        if mode == "drag":
            spinner.draggable = True

        shape = pymunk.Segment(spinner, (0,length), (0,-length), length/8.5)
        shape.elasticity = evalues[material]
        shape.friction = fvalues[material]
        shape.color = colors[material]
        shape.collision_type = COLL_SPINNER
        shape.layers = LAYER_FX_DYNAMICS | LAYER_DYNAMICS
        shape.material = material
        spinner.shape = shape        
        
        rot_body = pymunk.Body()
        rot_body.position = pos
        #rot_joint = pymunk.PinJoint( spinner, rot_body, (0,0), (0,0))
        rot_joint = pymunk.PivotJoint( spinner, rot_body, (0,0), (0,0))
        
        self.space.add( spinner, shape, rot_joint)
        self.spinners.append( spinner)
        return spinner
        
    def randcolor(self, color):
        value = random.uniform(0.3,1.0)
        return (int(color[0]*value), int(color[1]*value), int(color[2]*value))
    
    def make_particles(self, pos, number, color):
        #prevent massive fps drops
        if self.controller.fps < self.particle_fps_limit:
            return None
    
        #cap the total number of particles at any time
        if len( self.particles) +number > self.particle_limit:    
            number = self.particle_limit-len(self.particles)
    
        for i in xrange(number):
            angle = random.uniform( 0.0, 2*math.pi)
            vel = random.uniform(100.0, 300.0)
        
            body = pymunk.Body( 0.001, pymunk.inf)
            body.position = pos
            body.velocity = Vec2d( vel*math.sin(angle), vel*math.cos(angle))
            body.color = self.randcolor(color)
            body.life = random.uniform( 0.5, 2.0)
            body.apply_force( (0,200*body.mass))#force to reduce gravity on particles

            shape = pymunk.Circle( body, 0.75)
            shape.color = color
            shape.layers = LAYER_FX_STATICS | LAYER_FX_DYNAMICS
            shape.elasticity = 1.2
            shape.friction = 0.7

            body.shape = shape
            self.space.add( body, shape)
            self.particles.append( body)

    def make_victory(self, x, y, w, h):
        points = [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]
        vic = pymunk.Poly( self.space.static_body, points)
        vic.color = (255,255,0)
        vic.collision_type = COLL_VICTORY
        vic.topleft = Vec2d(x,y+h)
        vic.dimensions = Vec2d(w,h)
        vic.layers = LAYER_STATICS
        self.space.add( vic)
        self.victories.append(vic)
        return vic

    def make_forcefield(self, x, y, w, h, force):
        points = [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]
        
        field = pymunk.Poly( self.space.static_body, points)
        field.fieldforce = force
        field.center = Vec2d( x+w/2, y+h/2)
        field.layers = 0

        field.topleft = Vec2d(x,y+h)
        field.imgoffset = Vec2d(0,0)
        field.dimensions = Vec2d(w,h)

        self.space.add( field)
        self.forcefields.append( field)
        
    def reposition_player(self, pos, vel=None):
        self.player.position = pos
        if vel is not None:
            self.player.velocity = vel

    def make_player(self, position):
        mass = 10
        radius = 14
        player = pymunk.Body( mass, pymunk.inf)
        player.position = position
        player.joints = []
        player.dead = False
        player.facing = "right"

        shape = pymunk.Circle(player, radius)
        shape.color = (50,200,50)
        shape.elasticity = 1.0
        shape.friction = 0.5
        shape.collision_type = COLL_PLAYER
        shape.layers = LAYER_STATICS | LAYER_DYNAMICS

        self.space.add(player, shape)
        self.player = player
        self.player.shape = shape
        
    def make_gravball(self, pos, mode, size, wellsize):

        gb = pymunk.Body(pymunk.inf,pymunk.inf)
        gb.position = pos
        gb.size = size
        gb.strength = size*GRAVBALL_STREN
        gb.wellsize = wellsize
        gb.timer = -.1
        gb.life = GRAVBALL_LIFE
        gb.shutdown = False

        if mode == "push":
            gb.strength *= -1

        self.gravballs.append( gb)
        return gb

    def make_magnet(self, pos, size):
        body = pymunk.Body()
        body.position = pos
        circ = pymunk.Circle( body, size)
        circ.color = (180,180,180)
        circ.elasticity=0.01
        circ.collision_type = COLL_MAGNET
        circ.layers = LAYER_STATICS | LAYER_FX_STATICS  

        body.shape = circ
        self.space.add( circ)
        self.magnets.append( body)

    def make_enemy(self, pos, limits, dir):
        body = pymunk.Body( 10,pymunk.inf)
        body.dir = dir
        body.position = pos
        body.limits = limits
        w = 20
        h = 20
        points = [(-w,-h),(w,-h),(w,h),(-w,h)]
        square = pymunk.Poly( body, points)
        square.color = (0,0,255)
        square.elasticity = 0.5
        square.friction = 0.0
        square.collision_type = COLL_ENEMY
        square.layers = LAYER_STATICS | LAYER_DYNAMICS

        body.shape = square
        
        self.enemies.append( body)
        self.space.add( body, square)
        
        
    def reload_level(self):
 
        #reset various fields
        self.charging = False
        self.charge = 0
        self.charge_cap =  0
        self.player_impact = 0.0        
        self.grabbed = None
        self.mousepos = Vec2d(0,0)
        self.complex_drawing = True
        self.max_speed = 0
        self.player_launchable = True
        self.drag_joint = None
        self.player_floating = False
        self.player_float = 6000
        self.time = 0.0
        self.status_img = None
        self.status_offset = 0
        self.game_mode = GAME_NORMAL
        self.clear_status_text()

        #reset the space
        self.space = pymunk.Space()
        self.space.gravity = 0, GRAVITY
        self.space.add_collision_handler( COLL_PLAYER, COLL_MAGNET, begin=self.player_collide_with_sound, post_solve=self.player_magnet_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_VICTORY, pre_solve=self.player_victory_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_ENEMY, pre_solve=self.player_enemy_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_SPINNER, begin=self.player_collide_with_sound, pre_solve=self.player_spinner_collide)
        self.space.add_collision_handler( COLL_PLAYER, COLL_SEGMENT, pre_solve=self.player_segment_collide, begin=self.player_collide_with_sound)
        self.space.add_collision_handler( COLL_ENEMY, COLL_ENEMY, begin=self.cancel_collide)
        self.space.add_collision_handler( COLL_ENEMY, COLL_VICTORY, begin=self.cancel_collide)
        
        #reset the game objects
        self.make_player( (100, 100))    
        self.gravballs = []
        self.spinners = []
        self.magnets = []
        self.segments = []
        self.enemies = []
        self.forcefields = []
        self.victories = []
        self.particles = []
        
        title = None
        subtitle = None

        #create all of the elements
        for e in self.level_elements:

            if e.tag == "spinner":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                mode = get_attrib(e.attrib, "mode")
                speed = get_attrib(e.attrib, "speed", 0.0, float)
                angle = get_attrib(e.attrib, "angle", 0.0, float)
                length = get_attrib(e.attrib, "length", 60, float)
                mat = get_attrib(e.attrib, "material", None, int)
                self.make_spinner( mode, (x,y), angle, speed, length, mat)
            elif e.tag == "segment":
                x1 = get_attrib(e.attrib, "x1", None, float)
                x2 = get_attrib(e.attrib, "x2", None, float)
                y1 = get_attrib(e.attrib, "y1", None, float)
                y2 = get_attrib(e.attrib, "y2", None, float)
                size = get_attrib(e.attrib, "size", 11, int)
                mat = get_attrib(e.attrib, "material", 0, int)
                self.make_wall( (x1,y1), (x2,y2), mat, size)
            elif e.tag == "gravball":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                mode = get_attrib(e.attrib, "mode")
                size = get_attrib(e.attrib, "size", None, int)
                wellsize = get_attrib(e.attrib, "wellsize", None, int)
                self.make_gravball( Vec2d(x,y), mode, size, wellsize)
            elif e.tag == "magnet":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                size = get_attrib(e.attrib, "size", None, int)
                self.make_magnet( (x,y), size)                
            elif e.tag == "enemy":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                lim1 = get_attrib(e.attrib, "leftlimit", None, float)
                lim2 = get_attrib(e.attrib, "rightlimit", None, float)
                dir = get_attrib(e.attrib, "dir", 1, int)
                self.make_enemy( Vec2d(x,y), Vec2d(lim1,lim2), dir)
            elif e.tag == "player":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                self.reposition_player( (x,y), (0,0))
            elif e.tag == "victory":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                w = get_attrib(e.attrib, "w", None, float)
                h = get_attrib(e.attrib, "h", None, float)
                self.make_victory( x, y, w, h)
            elif e.tag == "forcefield":
                x = get_attrib(e.attrib, "x", None, float)
                y = get_attrib(e.attrib, "y", None, float)
                w = get_attrib(e.attrib, "w", None, float)
                h = get_attrib(e.attrib, "h", None, float)
                fx = get_attrib(e.attrib, "forcex", None, float)
                fy = get_attrib(e.attrib, "forcey", None, float)
                self.make_forcefield( x, y, w, h, Vec2d(fx, fy))
        
            elif e.tag == "title":
                title = e.text
                
            elif e.tag == "subtitle":
                subtitle = e.text
        
            else:
                print "unrecognized tag", e.tag
                
        self.static_img = pygame.Surface( self.screen_size, pygame.SRCALPHA)
        self.draw_statics( self.static_img)
        
        if title is not None:
            texts = [(50, title)]
            if subtitle is not None:
                texts.append( (30, subtitle))
            self.show_status_text( False, 2.0, texts)

    def enemy_enemy_collide(self, space, arbiter):
        return False                

    def cancel_collide(self, space, arbiter):
        return False
        
    def stick_player_to_magnet(self, bbody, sbody, pos, space):
        bbody.velocity = Vec2d(0,0)
        bbody.angular_velocity = 0
        bbody.group = 1
        pivot_joint = pymunk.PivotJoint(bbody, sbody, pos)
        pivot_joint.max_force = 50000.
        space.add(pivot_joint)
        bbody.joints = [pivot_joint]

    def player_magnet_collide(self, space, arbiter):
        player, spinner = arbiter.shapes
        pos = arbiter.contacts[0].position
        player.collision_type = 0#prevent this collision handler from being called again until the player launches again
        space.add_post_step_callback(self.stick_player_to_magnet, player.body, spinner.body, pos, self.space)
        self.player_launchable = True
        return True
        
    def player_spinner_collide(self, space, arbiter):
        self.player_launchable = True
        return True

    def player_victory_collide(self, space, arbiter):
        self.win_level()
        return True

    def player_gravball_collide(self, space, arbiter):
        player, gravball = arbiter.shapes
        gravball.body.timer = GRAVBALL_COOLDOWN
        return True
        
    def player_enemy_collide(self, space, arbiter):
        player, enemy = arbiter.shapes
        self.player_launchable = True
        playerspeed = player.body.velocity.get_length()
        speeddiff = (player.body.velocity - enemy.body.velocity).get_length()
        if playerspeed > 350:# and speeddiff > 100:
            self.space.remove( enemy, enemy.body)
            self.enemies.remove( enemy.body)
            self.make_particles( self.player.position, 125, ENEMY_PARTICLE_COLOR)
            snd = resources.get("sheepdie")
            snd.play()
        else:
            self.make_particles( self.player.position, 125, PLAYER_PARTICLE_COLOR)
            self.kill_player()
        return False
        
    def player_segment_collide(self, space, arbiter, *args, **kwargs):
        player, seg = arbiter.shapes
        self.player_launchable = True
        
        if seg.material == 3:
            self.kill_player()
        if arbiter.contacts[0].normal[1] < 0:
            self.player_grounded = True
        return True
        
    def player_collide_with_sound(self, space, arbiter, *args, **kwargs):
        player, obj = arbiter.shapes
        player = player.body
        self.player_launchable = True        
        vel = player.velocity.get_length()
        self.make_particles( player.position, int(vel/20), PLAYER_PARTICLE_COLOR)
        self.player_impact = PLAYER_IMPACT_TIME
        if vel >= 75.0:
            snd = resources.get( random.choice(("squish1", "squish2", "squish3", "squish4")))
            if hasattr( obj, "material") and obj.material == 1:
                    snd = resources.get( random.choice(("bounce1","bounce2","bounce3","bounce4")))
            snd.play()        
        return True
        
    def kill_player(self):
        sz1 = 50
        sz2 = 30
        sz3 = 18
        dietexts = (
            [(sz1, "You killed Bob"), (sz2, "I hope it was worth it")],
            [(sz1, "You killed Bob"), (sz2, "Just as I expected")],
            [(sz1, "You killed him!"), (sz2, "Do you feel like a man now?")],
            [(sz1, "Bob is dead!"), (sz2, "Way to go dumbass")],
            [(sz1, "How did you die there?"), (sz2, "Seriously!")],
            [(sz1, "Farewell Bob"), (sz2, "You will be missed")],
            [(sz1, "You suck"), (sz2, "Seriously what are you even doing?")],
        )    
        addendum = [(sz3, "Press Q to reload")]
    
        snd = resources.get( "playerdie")
        snd.play()
        self.space.remove( self.player, self.player.shape)
        self.player.dead = True
        self.game_mode = GAME_OVER
        self.show_status_text( True, -1.0, random.choice(dietexts)+addendum)
        
    def win_level(self):
        sz1 = 50
        sz2 = 30
        sz3 = 18
        wintexts = (
            [(sz1, "Good job"), (sz2, "Maybe try going outside some time")],
            [(sz1, "You won"), (sz2, "You want a trophy or something?")],
            [(sz1, "Good for you"), (sz2, "That was sarcasm by the way")],
            [(sz1, "You did it"), (sz2, "I could have done it faster")],
            [(sz1, "Wow"), (sz2, "A trained ape could have done better")],
            [(sz1, "Impressive"), (sz2, "But not as impressive as you think")],
        )
        addendum = [(sz3, "Press SPACE to continue")]
    
        self.game_mode = GAME_WON
        snd = resources.get("victory")
        snd.play()
        self.show_status_text( True, -1.0, random.choice( wintexts)+addendum)
     
    def pause_game(self):
        self.game_mode = GAME_PAUSE
        self.show_status_text( False, -1.0, [(50, "Game Paused"), (40, "Press space to resume"), (30, "Press q to restart level"), (25, "Press z to teleport like a dirty cheater")])
        
    def resume_game(self):
        self.game_mode = GAME_NORMAL
        self.clear_status_text()
        
    def start_next_level(self):
        config = {"level": self.levelnum+1}
        self.controller.start_activity( GameplayActivity, config)
        self.finish()


