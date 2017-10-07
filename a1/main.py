# Image manipulation
#
# You'll need Python 2.7 and must install these packages:
#
#   numpy, PyOpenGL, Pillow

import sys, os, numpy

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

# Image directory and pathe to image file

imgDir      = 'images'
imgFilename = 'mandrill.png'

imgPath = os.path.join( imgDir, imgFilename )



# File dialog

import Tkinter, tkFileDialog

root = Tkinter.Tk()
root.withdraw()


def hist_equalize():
  global current_image

  # Read image and convert to YCbCr
  current_image_pixels = current_image.convert( 'YCbCr' ).load()

  width  = current_image.size[0]
  height = current_image.size[1]

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

  return temp_image.convert( 'RGB' )



# Read and modify an image.

def buildImage():
  global current_image

  # Read image and convert to YCbCr
  current_image_pixels = current_image.convert( 'YCbCr' ).load()

  width  = current_image.size[0]
  height = current_image.size[1]

  # Set up a new, blank image of the same size

  new_image = Image.new( 'YCbCr', (width,height) )
  new_image_pixels = new_image.load()

  # Build destination image from source image

  for i in range(width):
    for j in range(height):

      # read source pixel
      
      y,cb,cr = current_image_pixels[i,j]

      # ---- MODIFY PIXEL ----

      y = int(contrast * y) + (brightness * 255) # TODO Normalize brightness before doing this

      # write destination pixel (while flipping the image in the vertical direction)
      
      new_image_pixels[i,height-j-1] = (y,cb,cr)

  # Done

  return new_image.convert( 'RGB' )



# Set up the display and draw the current image

def display():

  # Clear window

  glClearColor ( 1, 1, 1, 0 )
  glClear( GL_COLOR_BUFFER_BIT )

  # rebuild the image

  img = buildImage()

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

  global brightness, contrast, current_image

  if key == '\033': # ESC = exit
    sys.exit(0)

  elif key == 'l':
    path = tkFileDialog.askopenfilename( initialdir = imgDir )
    if path:
      loadImage( path )

  elif key == 's':
    outputPath = tkFileDialog.asksaveasfilename( initialdir = '.' )
    if outputPath:
      saveImage( outputPath )

  elif key == 'h':
    # Remove all previous corrections
    brightness = 0
    contrast = 1

    print current_image
    
    # Perform equalization
    current_image = hist_equalize().transpose(Image.FLIP_TOP_BOTTOM)

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

  global imgPath, contrast, brightness, current_image 
  imgPath = path
  
  current_image = Image.open( imgPath ).convert( 'YCbCr' )

  # Reset global parameters
  contrast = 1 # contrast by which luminance is scaled
  brightness = 0 # brightness by which luminance is scaled

def saveImage( path ):

  current_image.save( path )

  

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
  global contrast, brightness, current_image

  if state == GLUT_DOWN:

    button = btn
    initX = x
    initY = y
    initContrast = contrast
    initBrightness = brightness

  elif state == GLUT_UP:

    button = None
    
    # Set current image to new image
    current_image = buildImage().transpose(Image.FLIP_TOP_BOTTOM)
    contrast = 1
    brightness = 0


# Handle mouse motion

def motion( x, y ):

  diffX = x - initX
  diffY = y - initY

  global contrast
  global brightness

  contrast = initContrast + diffY / float(windowWidth)
  brightness = initBrightness + diffX / float(windowHeight)

  if contrast < 0:
    contrast = 0

  glutPostRedisplay()
  


# Load current image
current_image = Image.open( imgPath ).convert( 'YCbCr' )
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
