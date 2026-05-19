#Task 1
from OpenGL.GL import * 
from OpenGL.GLU import *
from OpenGL.GLUT import * 
import random

width, height = 1350, 720
background_brightness = 0

#2D Cordinate
def setup_projection():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width, 0.0, height, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)

#display
def display():
    glClearColor(background_brightness, background_brightness, background_brightness, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  

def ground():
    glBegin(GL_TRIANGLES)
    glColor3f(0.54, 0.27, 0.07)
    #left rectangle
    glVertex2f(0, 420)
    glVertex2f(width, 0)
    glVertex2f(0, 0)
    #right
    glVertex2f(width, 0)
    glVertex2f(width, 420)
    glVertex2f(0, 420)
    glEnd()

def tree():
    h = 80
    w = 50
    base = 360 # ->y axis
    x = 0
    while x < width:
        glBegin(GL_TRIANGLES)
        # Top
        glColor3f(0.0, 0.22, 0.0)
        glVertex2f(x + w / 2, base + h)
        # Bottom Left
        glColor3f(0.0, .87, 0.0)
        glVertex2f(x, base)
        # Bottom Right
        glColor3f(0.0, .87, 0.0)
        glVertex2f(x + w, base)
        glEnd()
        x += w + 12

def barir_chad():
    center = width / 2
    roof_w = 350
    base_y = 350
    top_y = 470
    glBegin(GL_TRIANGLES)
    glColor3f(0.3, 0.2, 0.5)
    #left
    glVertex2f(center - roof_w/2, base_y)
    #right
    glVertex2f(center + roof_w/2, base_y)
    #top
    glVertex2f(center, top_y)
    glEnd()

def triangle_to_square_wall():
    center = width / 2
    wall_w = 250
    base_y = 230
    top_y = 350
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.99, 0.82)
    #left
    glVertex2f(center - wall_w/2,base_y)
    glVertex2f(center - wall_w/2, top_y)
    glVertex2f(center + wall_w/2,top_y)
    #right
    glVertex2f(center - wall_w/2, base_y)
    glVertex2f(center + wall_w/2,base_y)
    glVertex2f(center + wall_w/2, top_y)
    glEnd()

def window():
    center = width / 2
    wall_w = 250
    wall_base = 200
    wall_top = 350
    size = 40
    y = (wall_base + wall_top)/2 - size/2
    left_x = center - wall_w/2 + 20
    right_x = center + wall_w/2 - 20 - size
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_TRIANGLES)

    #left
    glVertex2f(left_x, y)
    glVertex2f(left_x + size, y)
    glVertex2f(left_x + size, y + size)

    glVertex2f(left_x, y)
    glVertex2f(left_x, y + size)
    glVertex2f(left_x + size, y + size)

    #right
    glVertex2f(right_x, y)
    glVertex2f(right_x + size, y)
    glVertex2f(right_x + size, y + size)

    glVertex2f(right_x, y)
    glVertex2f(right_x, y + size)
    glVertex2f(right_x + size, y + size)

    glEnd()

    # Grid lines
    glColor3f(0,0,0)
    glBegin(GL_LINES)

    #left grid
    glVertex2f(left_x, y + size/2)
    glVertex2f(left_x + size, y + size/2)
    glVertex2f(left_x + size/2, y)
    glVertex2f(left_x + size/2, y + size)

    #right grid
    glVertex2f(right_x, y + size/2)
    glVertex2f(right_x + size, y + size/2)
    glVertex2f(right_x + size/2, y)
    glVertex2f(right_x + size/2, y + size)

    glEnd()

def door():
    center = width / 2
    wall_base = 230
    door_w = 60
    door_h = 90
    x_left = center - door_w/2
    x_right = center + door_w/2
    y_bottom = wall_base
    y_top = wall_base + door_h
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_TRIANGLES)
    #left
    glVertex2f(x_left, y_bottom)
    glVertex2f(x_right, y_bottom)
    glVertex2f(x_right, y_top)
    #right
    glVertex2f(x_left, y_bottom)
    glVertex2f(x_left, y_top)
    glVertex2f(x_right, y_top)
    glEnd()
    #door lock
    glPointSize(6)
    glColor3f(0,0,0)
    glBegin(GL_POINTS)
    glVertex2f(x_right - 10, y_bottom + door_h/2)
    glEnd()


num_drops = 120
# Initialize raindrops
drops = [
    {'x': random.randint(0, width), 
     'y': random.randint(height // 2, height)}
    for _ in range(num_drops)
]

slant = 0.0  
def draw_drops():
    glColor3f(0.3, 0.6, 1.0)
    glLineWidth(2)
    glBegin(GL_LINES)
    for d in drops:
        glVertex2f(d['x'], d['y'])
        glVertex2f(d['x'] + slant * 2, d['y'] - 28)
    glEnd()
    glLineWidth(1)

# Update raindrops
def update_drops():
    for d in drops:
        d['y'] -= 10
        if d['y'] < 0:  # reset at top
            d['x'] = random.randint(0, width)
            d['y'] = height

# Idle function
def idle_func():
    update_drops()
    glutPostRedisplay()

#Keyboard to adjust brightness
def keyboard(key, x, y):
    global background_brightness
    if key in (b"u", b"U"):
        background_brightness = min(1.0, background_brightness + 0.1)
    elif key in (b"d", b"D"):
        background_brightness = max(0.0, background_brightness - 0.1)

# Special keys to adjust slant
def special_keys(key, x, y):
    global slant
    if key == GLUT_KEY_LEFT:
        slant = max(slant - 0.7, -10)
    elif key == GLUT_KEY_RIGHT:
        slant = min(slant + 0.7, 10)

def setup_projection():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, width, 0.0, height, 0.0, 1.0)   # 2D coordinate system
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
def projection():
    setup_projection()
    display()
    ground()
    tree()
    barir_chad()
    triangle_to_square_wall()
    window()
    door()
    draw_drops()
    glutSwapBuffers()  

#----main----
glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(width, height)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"A_01_Task_01")
glutDisplayFunc(display)
glutDisplayFunc(projection)  
glutIdleFunc(idle_func)                  
glutKeyboardFunc(keyboard)     
glutSpecialFunc(special_keys) 
glutMainLoop()

#==========#####==========#

#Task 2
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

width, height = 1350, 720

speed = 1
blink = False
prev_time = time.time()
arr = []
stuck = False
m = 10

def setup_projection():
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)

def freeze_keyyboard(key, x, y):
    global stuck
    if key == b' ':
        stuck = not stuck

def mouse(button, state, x, y):
    global blink
    if stuck == True:
        return
    y = height - y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        direction_y,direction_x = random.choice([-1, 1]),random.choice([-1, 1])
        r,g,b = random.random(),random.random(), random.random()
        arr.append([x, y, direction_x, direction_y, r, g, b])
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        blink = not blink
def speacial_keys(key, x, y):
    global speed
    if stuck == True:
        return
    if key == GLUT_KEY_UP:
        speed += 1
    if key == GLUT_KEY_DOWN:
        if speed > 0.2:
            speed -= 0.2

def points():
    global blink
    curr_time = time.time()
    # print(curr_time)
    glPointSize(5)
    glBegin(GL_POINTS)
    for i in arr:
        if blink == True:
            if int(curr_time / 3) % 2 == 0:
                glColor3f(0.0, 0.0, 0.0)
            else:
                glColor3f(i[4], i[5], i[6])
        else:
            glColor3f(i[4], i[5], i[6])
        glVertex2f(i[0], i[1])
    glEnd()

def update_points(value):
    global prev_time
    time_diff = time.time() - prev_time
    prev_time = time.time()
    if stuck == True:
        glutTimerFunc(25, update_points, 0)
        return
    for i in range(len(arr)):
        x,y,direction_x,direction_y,r,g,b = arr[i]
        x += direction_x * speed * time_diff * 350
        y += direction_y * speed * time_diff * 350
        # Top
        if y > (height - m):
            y = height - m
            direction_y = -direction_y
        # Bottom
        if y < m:
            y = m
            direction_y = -direction_y
        # Right
        if x > (width - m):
            x = width - m
            direction_x = -direction_x
        # Left
        if x < m:
            x = m
            direction_x = -direction_x
        arr[i] = [x, y, direction_x, direction_y, r, g, b]
    glutPostRedisplay()
    glutTimerFunc(25, update_points, 0)  

def mouse(button, state, x, y):
    global blink
    if stuck == True:
        return
    y = height - y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        direction_y,direction_x = random.choice([-1, 1]),random.choice([-1, 1])
        r,g,b = random.random(),random.random(), random.random()
        arr.append([x, y, direction_x, direction_y, r, g, b])
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        blink = not blink

def speacial_keys(key):
    global speed
    if stuck == True:
        return
    if key == GLUT_KEY_UP:
        speed += 1
    if key == GLUT_KEY_DOWN:
        if speed > 0.2:
            speed -= 0.2

def projection():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()
    points()
    glutSwapBuffers()

glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)
glutInitWindowSize(width, height)
glutCreateWindow(b"A_01_Task_02")
glutDisplayFunc(projection)
glutMouseFunc(mouse)
glutSpecialFunc(speacial_keys)
glutKeyboardFunc(freeze_keyyboard)
glutTimerFunc(0, update_points, 0)
glutMainLoop()