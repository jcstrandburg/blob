import os

class AnimatedImage:

    _numframes = -1
    _imgsrc = None
    _frame_lengths = []
    _frame_images = []
    _cur_frame = -1
    _time = 0.0

    def __init__( self, filepath):

        f = file( filepath)
        pathbase = os.path.split( filepath)[0]
        self._imgsrc = os.path.join( pathbase, f.readline().strip())
        self._numframes = int( f.readline())
        self._frame_lengths = f.readline().split()

        if len( self._frame_lengths) != self._numframes:
            raise Exception( "Frame count mismatch when loading animation "+filepath)

        for i in range( self._numframes):
            self._frame_lengths[i] = float( self._frame_lengths[i])

        self._cur_frame = 0
        self._time = 0.0

        print self._imgsrc, self._numframes, self._frame_lengths
        pass

    def reset( self):
        print "resetting"
        pass  

    def cycle( self, time):
        self._time += time
        print "cycle"
        while self._time >= self._frame_lengths[ self._cur_frame]:
            self._time -= self._frame_lengths[ self._cur_frame]
            self._cur_frame = (self._cur_frame + 1)%self._numframes
            print "cycled to", self._cur_frame

    def get_current_image( self):
        pass


if __name__ == "__main__":
    
    anim = AnimatedImage( os.path.join( "res", "anim.ani"))      
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
    anim.cycle( 0.3)
        
