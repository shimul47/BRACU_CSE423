from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import time

def pixel_to_gl(px, py, w=800, h=600):
    return (px - w/2) / (w/2), (h/2 - py) / (h/2)

def gl_to_pixel(gx, gy, w=800, h=600):
    return (gx + 1.0) * w / 2, (1.0 - gy) * h / 2

def zone(dx, dy):
    if abs(dx) >= abs(dy) and dx > 0 and dy > 0:
        return 0
    elif abs(dy) > abs(dx) and dx > 0 and dy > 0:
        return 1
    elif abs(dy) > abs(dx) and dx <= 0 and dy > 0:
        return 2
    elif abs(dx) >= abs(dy) and dx <= 0 and dy > 0:
        return 3
    elif abs(dx) >= abs(dy) and dx <= 0 and dy <= 0:
        return 4
    elif abs(dy) > abs(dx) and dx <= 0 and dy <= 0:
        return 5
    elif abs(dy) > abs(dx) and dx > 0 and dy <= 0:
        return 6
    else:
        return 7

def zone_x_to_zone_0(x, y, z):
    if z == 0:
        return (x, y)
    elif z == 1:
        return (y, x)
    elif z == 2:
        return (y, -x)
    elif z == 3:
        return (-x, y)
    elif z == 4:
        return (-x, -y)
    elif z == 5:
        return (-y, -x)
    elif z == 6:
        return (-y, x)
    else:
        return (x, -y)

def zone_o_to_zone_x(x, y, z):
    if z == 0:
        return (x, y)
    elif z == 1:
        return (y, x)
    elif z == 2:
        return (-y, x)
    elif z == 3:
        return (-x, y)
    elif z == 4:
        return (-x, -y)
    elif z == 5:
        return (-y, -x)
    elif z == 6:
        return (y, -x)
    else:
        return (x, -y)

def mlp_line_zone_0(x0, y0, x1, y1):
    pts = []
    dx = x1 - x0
    dy = y1 - y0
    d = 2 * dy - dx
    e = 2 * dy
    ne = 2 * (dy - dx)
    y = y0
    for x in range(int(x0), int(x1) + 1):
        pts.append((x, y))
        if d > 0:
            d = d + ne
            y = y + 1
        else:
            d = d + e
    return pts

def plot(x0, y0, x1, y1, rgb):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    
    if x0 == x1 and y0 == y1:
        glColor3f(*rgb)
        glBegin(GL_POINTS)
        gx, gy = pixel_to_gl(x0, y0, 800, 600)
        glVertex2f(gx, gy)
        glEnd()
        return
    
    dx = x1 - x0
    dy = y1 - y0
    z = zone(dx, dy)
    x0z, y0z = zone_x_to_zone_0(x0, y0, z)
    x1z, y1z = zone_x_to_zone_0(x1, y1, z)
    pts = mlp_line_zone_0(int(x0z), int(y0z), int(x1z), int(y1z))
    
    glColor3f(*rgb)
    glBegin(GL_POINTS)
    for px, py in pts:
        fx, fy = zone_o_to_zone_x(px, py, z)
        gx, gy = pixel_to_gl(fx, fy, 800, 600)
        glVertex2f(gx, gy)
    glEnd()

def new_drop():
    return {'x': random.uniform(-0.8, 0.8),'y': 0.95,'r': 0.08,'v': 0.010,'c': (random.random() * 0.7 + 0.3, random.random() * 0.7 + 0.3, random.random() * 0.7 + 0.3), 'on': True }

def draw_drop(d):
    if not d['on']:
        return
    cx, cy = gl_to_pixel(d['x'], d['y'], 800, 600)
    r = d['r'] * 300
    plot(cx, cy - r, cx + r, cy, d['c'])
    plot(cx + r, cy, cx, cy + r, d['c'])
    plot(cx, cy + r, cx - r, cy, d['c'])
    plot(cx - r, cy, cx, cy - r, d['c'])

def tick_drop(d, s):
    d['y'] -= d['v'] * s
    if d['y'] < -1.1:
        d['on'] = False

def draw_bat(b):
    px, py = gl_to_pixel(b['x'], b['y'], 800, 600)
    w, h = b['w'] * 400, b['h'] * 295
    plot(px - w, py, px - w * 0.6, py + h, b['c'])
    plot(px - w * 0.6, py + h, px + w * 0.6, py + h, b['c'])
    plot(px + w * 0.6, py + h, px + w, py, b['c'])
    plot(px + w, py, px - w, py, b['c'])

def bat_left(b):
    if b['x'] - b['w'] > -1.0:
        b['x'] -= 0.02

def bat_right(b):
    if b['x'] + b['w'] < 1.0:
        b['x'] += 0.02

def bat_auto(b, tx):
    tx = max(-1.0 + b['w'], min(tx, 1.0 - b['w']))
    diff = tx - b['x']
    if abs(diff) > 0.015:
        move = max(-0.035, min(0.035, diff * 0.35))
        b['x'] += move
    else:
        b['x'] = tx

def check_hit(d, b):
    return abs(d['x'] - b['x']) < d['r'] + 0.2 and abs(d['y'] - b['y']) < d['r'] 

def draw_btn(btn, pause):
    px, py = gl_to_pixel(btn['x'], btn['y'], 800, 600)
    sz = btn['s'] * 200
    bid = btn['id']
    c = btn['c']
    
    if bid == 0:
        plot(px - sz * 0.2, py, px + sz * 0.3, py, c)
        plot(px - sz * 0.2, py, px - sz * 0.05, py - sz * 0.25, c)
        plot(px - sz * 0.2, py, px - sz * 0.05, py + sz * 0.25, c)
    elif bid == 1:
        if not pause:
            plot(px - sz * 0.15, py - sz * 0.3, px - sz * 0.15, py + sz * 0.3, c)
            plot(px + sz * 0.15, py - sz * 0.3, px + sz * 0.15, py + sz * 0.3, c)
        else:
            plot(px - sz * 0.2, py - sz * 0.3, px + sz * 0.3, py, c)
            plot(px + sz * 0.3, py, px - sz * 0.2, py + sz * 0.3, c)
            plot(px - sz * 0.2, py + sz * 0.3, px - sz * 0.2, py - sz * 0.3, c)
    elif bid == 2:
        plot(px - sz * 0.3, py - sz * 0.3, px + sz * 0.3, py + sz * 0.3, c)
        plot(px - sz * 0.3, py + sz * 0.3, px + sz * 0.3, py - sz * 0.3, c)


def btn_hit(btn, gx, gy):
    return abs(gx - btn['x']) < btn['s'] and abs(gy - btn['y']) < btn['s']

game = {'bat': {'x': 0.0, 'y': -0.85, 'w': 0.2, 'h': 0.15, 'c': (1.0, 1.0, 1.0)},'drop': None,'score': 0,'end': False,'pause': False,'cheat': False,'start_time': time.time(),'mul': 1.0, 'keys': {}}
game['drop'] = new_drop()
game['b1'] = {'x': -0.9, 'y': 0.9, 's': 0.28, 'id': 0, 'c': (0.0, 1.0, 1.0)}
game['b2'] = {'x': 0.0, 'y': 0.9, 's': 0.28, 'id': 1, 'c': (1.0, 0.65, 0.0)}
game['b3'] = {'x': 0.9, 'y': 0.9, 's': 0.28, 'id': 2, 'c': (1.0, 0.0, 0.0)}

def update():
    if game['end'] or game['pause']:
        return
    
    keys = [k for k, v in game['keys'].items() if v]
    if b'left arrow' in keys:
        bat_left(game['bat'])
    if b'right arrow' in keys:
        bat_right(game['bat'])
    
    game['mul'] = 1.0 + (time.time() - game['start_time']) / 10.0
    tick_drop(game['drop'], game['mul'])
    
    if game['cheat']:
        bat_auto(game['bat'], game['drop']['x'])
    
    if check_hit(game['drop'], game['bat']):
        game['score'] += 1
        print(f"Score: {game['score']}")
        game['drop'] = new_drop()
    
    if not game['drop']['on']:
        game['end'] = True
        game['bat']['c'] = (1.0, 0.0, 0.0)
        print(f"Game Over! Score: {game['score']}")

def render():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_drop(game['drop'])
    draw_bat(game['bat'])
    draw_btn(game['b1'], game['pause'])
    draw_btn(game['b2'], game['pause'])
    draw_btn(game['b3'], game['pause'])
    glutSwapBuffers()

def key_down(k, x, y):
    if k == b'\x1b':
        print(f"Goodbye: {game['score']}")
        glutLeaveMainLoop()
    elif k == b'c' or k == b'C':
        if not game['end']:
            game['cheat'] = not game['cheat']
            if game['cheat']:
                print("Cheat On")
            else:
                print("Cheat Off")
    else:
        game['keys'][k] = True

def key_up(k, x, y):
    if k in game['keys']:
        game['keys'][k] = False

def special_down(k, x, y):
    if k == GLUT_KEY_LEFT:
        game['keys'][b'left arrow'] = True
    elif k == GLUT_KEY_RIGHT:
        game['keys'][b'right arrow'] = True

def special_up(k, x, y):
    if k == GLUT_KEY_LEFT:
        game['keys'][b'left arrow'] = False
    elif k == GLUT_KEY_RIGHT:
        game['keys'][b'right arrow'] = False

def mouse_click(b, s, x, y):
    if b == GLUT_LEFT_BUTTON and s == GLUT_DOWN:
        gx, gy = pixel_to_gl(x, y)
        if btn_hit(game['b1'], gx, gy):
            print("Restart")
            game['drop'] = new_drop()
            game['bat'] = {'x': 0.0, 'y': -0.85, 'w': 0.2, 'h': 0.15, 'c': (1.0, 1.0, 1.0)}
            game['score'] = 0
            game['end'] = False
            game['pause'] = False
            game['cheat'] = False
            game['start_time'] = time.time()
        elif btn_hit(game['b2'], gx, gy):
            if not game['end']:
                game['pause'] = not game['pause']
                print(f"{'PAUSED' if game['pause'] else 'PLAY'}")
        elif btn_hit(game['b3'], gx, gy):
            print(f"Goodbye: {game['score']}")
            glutLeaveMainLoop()

def display():
    update()
    render()
def timer(v):
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

print("CATCH THE DIAMONDS")

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(800, 600)
glutInitWindowPosition(50, 50)
glutCreateWindow(b"Catch Diamonds")

glClearColor(0.0, 0.0, 0.0, 1.0)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluOrtho2D(-1.0, 1.0, -1.0, 1.0)
glMatrixMode(GL_MODELVIEW)
glPointSize(2.0)

glutDisplayFunc(display)
glutKeyboardFunc(key_down)
glutKeyboardUpFunc(key_up)
glutSpecialFunc(special_down)
glutSpecialUpFunc(special_up)
glutMouseFunc(mouse_click)
glutTimerFunc(16, timer, 0)

glutMainLoop()