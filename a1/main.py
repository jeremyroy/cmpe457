# Image manipulation
#
# You'll need Python 2.7 and must install these packages:
#
#   numpy, PyOpenGL, Pillow

# TODO: display temporary image, store current image on button unclick

import sys, os, numpy, Queue

try: # Pillow
  from PIL import Image
except:
  print 'Error: Pillow has not been installed.'
  sys.exit(0)

try: # PyOpenGL
  from OpenGL.GLUT import *
  from OpenGL.GL import *
  from OpenGL.GLU import *
except:
  print 'Error: PyOpenGL has not been installed.'
  sys.exit(0)



# Globals

windowWidth  = 600 # window dimensions
windowHeight =  800

contrast = 1 # contrast by which luminance is scaled
brightness = 0 # brightness by which luminance is scaled

current_image = None
temp_draw_image = None
current_filter = None

current_image_pixels = None
temp_draw_pixels = None

c_rad = 20

# Image directory and path to image file

imgDir      = 'images'
imgFilename = 'mandrill.png'

imgPath = os.path.join( imgDir, imgFilename )

# Filer directory and path to filter file
filterDir      = 'filters'

# File dialog

import Tkinter, tkFileDialog

root = Tkinter.Tk()
root.withdraw()


def hist_equalize():
  global current_image, current_image_pixels

  width  = current_image.size[0]
  height = current_image.size[1]

  # Convert image to YCbCr if not already in this format
  if (current_image.mode != 'YCbCr'):
    current_image = current_image.convert( 'YCbCr' )
    current_image_pixels = current_image.load()

  # Set up a new, blank image of the same size

  temp_image = Image.new( 'YCbCr', (width,height) )
  temp_image_pixels = temp_image.load()

  # Build histogram from source image
  histogram = [0] * 256

  for i in range(width):
    for j in range(height):

      # read source pixel
      
      y,cb,cr = current_image_pixels[i,j]
      
      if (y > 255):
        y = 255
      elif (y < 0):
        y = 0

      # ---- CREATE HISTOGRAM ----

      histogram[y] += 1

  # Apply histogram to temp image

  for i in range(width):
    for j in range(height):

      # read source pixel
      
      y,cb,cr = current_image_pixels[i,j]

      # apply histogram correction

      y = ( 256.0 / (width * height) ) * sum( histogram[0:int(y)] ) - 1
      y = int( round(y) )

      # write destination pixel (while flipping the image in the vertical direction)
      
      temp_image_pixels[i,height-j-1] = (y,cb,cr)

  # Done

  current_image = temp_image.transpose(Image.FLIP_TOP_BOTTOM)
  current_image_pixels = current_image.load()


# Apply filter by convolution

def applyFilter():

  global current_filter, current_image, current_image_pixels

  print "Starting convolution"

  # Convert image to RGB if not already in this format
  if (current_image.mode != 'RGB'):
    current_image = current_image.convert( 'RGB' )
    current_image_pixels = current_image.load()

  # If no filter loaded, load a filter

  if current_filter == None:
    path = tkFileDialog.askopenfilename( initialdir = filterDir )
    loadFilter(path)

  # Find origin of filter - assume origin = center

  f_width  = len(current_filter[0])
  f_height = len(current_filter)
  orig_x   = f_width / 2 
  orig_y   = f_height / 2

  # Flip filter for convolution
 
  flipped_filter = list(reversed(current_filter))

  for i in range(len(flipped_filter)):
    flipped_filter[i] = list(reversed(flipped_filter[i]))

  # Calculate convenient variables

  width  = current_image.size[0]
  height = current_image.size[1]

  # Set up a new, blank image of the same size

  new_image = Image.new( 'RGB', (width,height) )
  new_image_pixels = new_image.load()

  # Perform convolution

  for i in range(width):
    for j in range (height):

      new_r = 0
      new_g = 0
      new_b = 0

      for f_i in range(-orig_x, orig_x + 1):
        for f_j in range(-orig_y, orig_y + 1):
          if ( 0 <= (i + f_i) < width ) and ( 0 <= (j + f_j) < height ):
            # read source pixel
      
            r,g,b = current_image_pixels[i+f_i ,j+f_j]

            # Calculate partial sum

            new_r += flipped_filter[orig_y + f_j][orig_x + f_i] * r
            new_g += flipped_filter[orig_y + f_j][orig_x + f_i] * g
            new_b += flipped_filter[orig_y + f_j][orig_x + f_i] * b

      # write destination pixel (while flipping the image in the vertical direction)

      new_image_pixels[i,height-j-1] = (int(new_r),int(new_g),int(new_b))

  # Done

  print "Finished convolution"

  current_image = new_image.transpose(Image.FLIP_TOP_BOTTOM)
  current_image_pixels = current_image.load()



def applyFilterAroundPoint(x, y):
  
  global current_filter, c_rad, current_image, current_image_pixels
  global temp_draw_image, temp_draw_pixels

  # Convert image to RGB if not already in this format
  if (temp_draw_image.mode != 'RGB'):
    temp_draw_image = temp_draw_image.convert( 'RGB' )
    temp_draw_pixels = temp_draw_image.load()

  if (current_image.mode != 'RGB'):
    current_image = current_image.convert( 'RGB' )
    current_image_pixels = current_image.load()

  # If no filter loaded, load a filter

  if current_filter == None:
    path = tkFileDialog.askopenfilename( initialdir = filterDir )
    loadFilter(path)

  # Find origin of filter - assume origin = center

  f_width  = len(current_filter[0])
  f_height = len(current_filter)
  orig_x   = f_width / 2 
  orig_y   = f_height / 2

  # Flip filter for convolution
 
  flipped_filter = list(reversed(current_filter))

  for i in range(len(flipped_filter)):
    flipped_filter[i] = list(reversed(flipped_filter[i]))
 
  # Calculate convenient variables

  width  = current_image.size[0]
  height = current_image.size[1]

  # Perform convolution around point (x,y)

  for i in range(x - c_rad, x + c_rad):
    for j in range(y - c_rad, y + c_rad):

      # Check if current pixel is out of range

      if (0 <= i < width) and (0 <= j < height):

        # Check if pixel is within radius of point x,y

        dist_from_point = numpy.sqrt( pow(x-i,2) + pow(y-j,2) )

        # Check if convolution already performed at point
        if (current_image_pixels[i,j] == temp_draw_pixels[i,height-j-1] ):
          continue

        if dist_from_point <= c_rad:

          # Perform convolution on this point

          new_r = 0
          new_g = 0
          new_b = 0

          for f_i in range(-orig_x, orig_x + 1):
            for f_j in range(-orig_y, orig_y + 1):
              if ( 0 <= (i + f_i) < width ) and ( 0 <= (j + f_j) < height ):
                # read source pixel

                r,g,b = current_image_pixels[i+f_i ,height - 1 - (j+f_j)]

                # Calculate partial sum

                new_r += flipped_filter[orig_y + f_j][orig_x + f_i] * r
                new_g += flipped_filter[orig_y + f_j][orig_x + f_i] * g
                new_b += flipped_filter[orig_y + f_j][orig_x + f_i] * b

          # write destination pixel (while flipping the image in the vertical direction)
      
          temp_draw_pixels[i,height-j-1] = (int(new_r),int(new_g),int(new_b))

  # Done
  #current_image = temp_draw_image
  #current_image_pixels = current_image.load()


def draw_black_line(x,y):
  global current_image, current_image_pixels
  
  width  = current_image.size[0]
  height = current_image.size[1]

  #new_image = Image.new( 'YCbCr', (width,height) )
  #new_image_pixels = new_image.load()

  # Queue changes

  #my_queue = Queue.Queue(0)
  #my_queue.put([x,y,0])

  # Apply queued changes
  #x,y,intensity = my_queue.get()
  #current_image

  new_image = current_image.transpose(Image.FLIP_TOP_BOTTOM)
  new_image_pixels = new_image.load()

  intensity,cb,cr = current_image_pixels[x,y]
      
  new_image_pixels[x,y] = (0,cb,cr)

  current_image = new_image.transpose(Image.FLIP_TOP_BOTTOM)
  current_image_pixels = current_image.load()

# Read and modify an image.

def buildImage():
  global temp_draw_image, temp_draw_pixels

  width  = temp_draw_image.size[0]
  height = temp_draw_image.size[1]

  # Convert image to YCbCr if not already in this format
  if (temp_draw_image.mode != 'YCbCr'):
    temp_draw_image = temp_draw_image.convert( 'YCbCr' )
    temp_draw_pixels = temp_draw_image.load()

  # Build destination image from source image

  for i in range(width):
    for j in range(height):

      # read source pixel
      
      y,cb,cr = temp_draw_pixels[i,j]

      # ---- MODIFY PIXEL ----

      y = int(contrast * y) + (brightness * 255) # TODO Normalize brightness before doing this

      # write destination pixel (while flipping the image in the vertical direction)
      
      temp_draw_pixels[i,j] = (y,cb,cr)

  # Done


# Set up the display and draw the current image

def display():
  global current_image, temp_draw_image, button

  # Clear window

  glClearColor ( 1, 1, 1, 0 )
  glClear( GL_COLOR_BUFFER_BIT )

  # rebuild the image
  if button == None:
    print "draw_current_image"
    draw_image = current_image.transpose(Image.FLIP_TOP_BOTTOM)
  else:
    print "draw temp_image"
    draw_image = temp_draw_image.transpose(Image.FLIP_TOP_BOTTOM)

  if draw_image.mode != 'RGB':
    img = draw_image.convert( 'RGB' )
  else:
    img = draw_image


  width  = img.size[0]
  height = img.size[1]

  # Find where to position lower-left corner of image

  baseX = (windowWidth-width)/2
  baseY = (windowHeight-height)/2

  glWindowPos2i( baseX, baseY )

  # Get pixels and draw

  imageData = numpy.array( list( img.getdata() ), numpy.uint8 )

  glDrawPixels( width, height, GL_RGB, GL_UNSIGNED_BYTE, imageData )

  glutSwapBuffers()


  
# Handle keyboard input

def keyboard( key, x, y ):

  global brightness, contrast, current_image, c_rad

  if key == '\033': # ESC = exit
    sys.exit(0)

  elif key == 'l':
    path = tkFileDialog.askopenfilename( initialdir = imgDir )
    if path:
      loadImage( path )

  elif key == 'f':
    path = tkFileDialog.askopenfilename( initialdir = filterDir )
    if path:
      loadFilter( path )

  elif key == 's':
    outputPath = tkFileDialog.asksaveasfilename( initialdir = '.' )
    if outputPath:
      saveImage( outputPath )

  elif key == 'a':
    applyFilter()

  elif key == 'h':
    # Remove all previous corrections
    brightness = 0
    contrast = 1

    # Perform equalization
    hist_equalize()

  elif key == '-' or key == '_':
    c_rad -= 1
    print "r = " + str(c_rad)

  elif key == '+' or key == '=':
    c_rad += 1
    print "r = " + str(c_rad)

  else:
    print 'key =', key    # DO NOT REMOVE THIS LINE.  It will be used during automated marking.

  glutPostRedisplay()



# Load and save images.
#
# Modify these to load to the current image and to save the current image.
#
# DO NOT CHANGE THE NAMES OR ARGUMENT LISTS OF THESE FUNCTIONS, as
# they will be used in automated marking.

def loadImage( path ):

  global imgPath, contrast, brightness, current_image, current_image_pixels
  imgPath = path
  
  current_image = Image.open( imgPath )
  current_image_pixels = current_image.load()

  # Reset global parameters
  contrast = 1 # contrast by which luminance is scaled
  brightness = 0 # brightness by which luminance is scaled

def saveImage( path ):

  if (current_image.mode == 'RGB'):
    current_image.save( path )
  else:
    current_image.convert( 'RGB').save( path )


def loadFilter( path ):
  global current_filter

  # Load filter info memory
  filter_file = open(path,"r")
  xdim, ydim = map(int, filter_file.readline().split())
  scale_factor = float(filter_file.readline())
  
  current_filter = [0] * ydim

  for i in range(ydim):
    current_filter[i] = map(int, filter_file.readline().split())
  
  filter_file.close()

  # Apply scale factor filter
  current_filter = [[float(j)*scale_factor for j in i] for i in current_filter]

# Handle window reshape

def reshape( newWidth, newHeight ):

  global windowWidth, windowHeight

  windowWidth  = newWidth
  windowHeight = newHeight

  glutPostRedisplay()



# Mouse state on initial click

button = None
initX = 0
initY = 0
initContrast = 1
initBrightness = 0


# Handle mouse click/unclick

def mouse( btn, state, x, y ):

  global button, initX, initY, initContrast, initBrightness
  global contrast, brightness
  global current_image, current_image_pixels
  global temp_draw_image, temp_draw_pixels

  if state == GLUT_DOWN:

    button = btn
    initX = x
    initY = y
    initContrast = contrast
    initBrightness = brightness
    temp_draw_image = current_image.copy()
    temp_draw_pixels = temp_draw_image.load()

  elif state == GLUT_UP:

    button = None
    
    # Set current image to new image
    buildImage()
    contrast = 1
    brightness = 0
    current_image = temp_draw_image.copy()
    current_image_pixels = current_image.load()


# Handle mouse motion

def motion( x, y ):

  global current_image

  if button == GLUT_LEFT_BUTTON:

    diffX = x - initX
    diffY = y - initY

    global contrast
    global brightness

    contrast = initContrast + diffY / float(windowWidth)
    brightness = initBrightness + diffX / float(windowHeight)

    if contrast < 0:
      contrast = 0

  elif button == GLUT_RIGHT_BUTTON:
    print str(x) + "," + str(y)

    width  = current_image.size[0]
    height = current_image.size[1]

    baseX = (windowWidth-width)/2
    baseY = (windowHeight-height)/2

    x = x - baseX
    y = (windowHeight - y) - baseY

    print str(x) + "," + str(y)

    # applyFilter()
    applyFilterAroundPoint(x,y)
    # draw_black_line(x,y)
    print "Displaying"

  glutPostRedisplay()



# Load current image
current_image = Image.open( imgPath )
current_image_pixels = current_image.load()
print current_image
    
# Run OpenGL

glutInit()
glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
glutInitWindowSize( windowWidth, windowHeight )
glutInitWindowPosition( 50, 50 )

glutCreateWindow( 'imaging' )

glutDisplayFunc( display )
glutKeyboardFunc( keyboard )
glutReshapeFunc( reshape )
glutMouseFunc( mouse )
glutMotionFunc( motion )

glutMainLoop()
