from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math
import random
import time


window_w = 1000
window_h = 800

field_view = 130
aspect = window_w / window_h
background = (0.0, 0.0, 0.0)

ARENA_HALF = 600
CELL = 60

PLAYER_SPEED = 7.5
TURN_SPEED = 3.0
TORSO_CENTER_Z = 90.0
HEAD_Z = 65.0

ENEMY_SPEED = 10.0
ENEMY_RADIUS = 30.0
ENEMY_COUNT = 5

BULLET_SPEED = 400.0
BULLET_RENDER_SCALE = 7
MISS_LIMIT = 10

CHEAT_ROTATE_SPEED = 4.0
CHEAT_FIRE_INTERVAL = 0.08
CHEAT_ANGLE_THRESHOLD = 10.0

THIRD_ORBIT = 0.0
THIRD_CAM_R = 400.0
THIRD_CAM_Z = 200

TEXT_FONT = globals().get("GLUT_BITMAP_HELVETICA_18")
if TEXT_FONT is None:
    TEXT_FONT = globals().get("GLUT_BITMAP_9_BY_15")


player_pos = [0.0, 0.0, 0.0]
rotation_angle = 5

fps = False
game_over = False

life_limit = 5
score = 0
miss = 0

cheat_mode = False
auto_gun_follow = False
cheat_fire_cooldown = 0.0

move_forward = False
move_back = False
turn_left = False
turn_right = False

bullets = []
enemies = []

last_tick = None


def clamp(value, low, high):
    return max(low, min(high, value))


def rgb(r, g, b):
    glColor3f(r, g, b)


def forward_vec(deg):
    radians = math.radians(deg)
    return [-math.cos(radians), -math.sin(radians)]

def xy_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def spawn_enemy_pos():
    x = random.uniform(-ARENA_HALF * 0.8, ARENA_HALF * 0.8)
    y = random.uniform(ARENA_HALF * 0.35, ARENA_HALF * 0.8)
    return [x, y, 0.0]

def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_w, 0, window_h)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(TEXT_FONT, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(rotation_angle, 0, 0, 1)

    if game_over:
        glRotatef(90, 1, 0, 0)

    if fps:
        sway = math.sin(math.radians(rotation_angle)) * 4.0

        rgb(0.84, 0.84, 0.84)
        glPushMatrix()
        glTranslatef(sway * 0.25, -18, 136)
        gluSphere(gluNewQuadric(), 10, 12, 12)
        glPopMatrix()

        rgb(1, 0.878, 0.741)
        for hand_x in (-18, 18):
            glPushMatrix()
            glTranslatef(hand_x + sway * (0.35 if hand_x < 0 else -0.35), -20, 104)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(gluNewQuadric(), 5, 4, 34, 8, 8)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()
    else:
        rgb(0.1, 0.5, 0.1)
        glPushMatrix()
        glTranslatef(0, 0, 90)
        glScalef(0.5, 1, 1)
        glutSolidCube(60)
        glPopMatrix()

        rgb(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, 0, 150)
        gluSphere(gluNewQuadric(), 25, 10, 10)
        glPopMatrix()

        rgb(0, 0, 1)
        for i in (-15, 15):
            glPushMatrix()
            glTranslatef(-15, i, 0)
            gluCylinder(gluNewQuadric(), 7, 12, 60, 10, 10)
            glPopMatrix()

        rgb(0.753, 0.753, 0.753)
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()

        rgb(1, 0.878, 0.741)
        for hand_y in (-25, 25):
            glPushMatrix()
            glTranslatef(-20, hand_y, 100)
            glRotatef(-90, 0, 1, 0)
            gluCylinder(gluNewQuadric(), 10, 6, 30, 10, 10)
            glPopMatrix()

    glPopMatrix()

def draw_enemy(enemy):
    radius = enemy["r"] * (1.12 + 0.10 * math.sin(enemy["phase"]))
    glPushMatrix()
    glTranslatef(enemy["p"][0], enemy["p"][1], enemy["p"][2] + radius)
    rgb(0.9, 0.1, 0.1)
    gluSphere(gluNewQuadric(), radius, 24, 24)
    rgb(0.0, 0.0, 0.0)
    glTranslatef(0, 0, radius * 0.8)
    gluSphere(gluNewQuadric(), radius * 0.55, 16, 16)
    glPopMatrix()

def draw_bullet(bullet):
    glPushMatrix()
    glTranslatef(bullet["p"][0], bullet["p"][1], bullet["p"][2])
    glScalef(BULLET_RENDER_SCALE, BULLET_RENDER_SCALE, BULLET_RENDER_SCALE)
    rgb(1.0, 0.0, 0.0)
    glutSolidCube(1)
    glPopMatrix()

def draw_arena():
    white = (1.0, 1.0, 1.0)
    purple = (0.7, 0.5, 0.95)

    glBegin(GL_QUADS)
    for x in range(-ARENA_HALF, ARENA_HALF, CELL):
        for y in range(-ARENA_HALF, ARENA_HALF, CELL):
            rgb(*(white if ((x // CELL + y // CELL) & 1) == 0 else purple))
            glVertex3f(x, y, 0)
            glVertex3f(x + CELL, y, 0)
            glVertex3f(x + CELL, y + CELL, 0)
            glVertex3f(x, y + CELL, 0)
    glEnd()

    wall_h = 108

    glBegin(GL_QUADS)
    rgb(0.1, 0.1, 0.9)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, wall_h)
    glVertex3f(-ARENA_HALF, ARENA_HALF, wall_h)
    glVertex3f(-ARENA_HALF, ARENA_HALF, 0)
    glEnd()

    glBegin(GL_QUADS)
    rgb(0.1, 0.9, 0.1)
    glVertex3f(ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(ARENA_HALF, -ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, ARENA_HALF, 0)
    glEnd()

    glBegin(GL_QUADS)
    rgb(0.1, 0.9, 0.9)
    glVertex3f(-ARENA_HALF, ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, ARENA_HALF, 0)
    glEnd()

    glBegin(GL_QUADS)
    rgb(0.3, 0.3, 0.3)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, 0)
    glVertex3f(-ARENA_HALF, -ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, -ARENA_HALF, wall_h)
    glVertex3f(ARENA_HALF, -ARENA_HALF, 0)
    glEnd()

def reset_game():
    global life_limit, score, miss, game_over, rotation_angle
    global cheat_mode, auto_gun_follow, cheat_fire_cooldown

    player_pos[:] = [0.0, 0.0, 0.0]
    rotation_angle = 90.0

    life_limit = 5
    score = 0
    miss = 0
    game_over = False

    cheat_mode = False
    auto_gun_follow = False
    cheat_fire_cooldown = 0.0

    bullets.clear()
    enemies.clear()
    for _ in range(ENEMY_COUNT):
        enemies.append({"p": spawn_enemy_pos(), "r": ENEMY_RADIUS, "phase": random.uniform(0, math.pi * 2)})

def fire(target_pos=None):
    if game_over == True:
        return
    sx, sy, sz = player_pos[0], player_pos[1], TORSO_CENTER_Z
    if target_pos is None:
        dx, dy = forward_vec(rotation_angle)
    else:
        vx = target_pos[0] - sx
        vy = target_pos[1] - sy
        length = math.hypot(vx, vy) + 1e-6
        dx = vx / length
        dy = vy / length

    bullets.append({"p": [sx, sy, sz], "d": [dx, dy, 0.0]})

def update_player(dt):
    global rotation_angle

    if turn_left:
        rotation_angle += TURN_SPEED * (dt * 60.0)
    if turn_right:
        rotation_angle -= TURN_SPEED * (dt * 60.0)
    if move_forward or move_back:
        move_angle = math.radians(rotation_angle)
        step = PLAYER_SPEED * (dt * 60.0)

        if move_forward:
            player_pos[0] -= math.cos(move_angle) * step
            player_pos[1] -= math.sin(move_angle) * step
        if move_back:
            player_pos[0] += math.cos(move_angle) * step
            player_pos[1] += math.sin(move_angle) * step

    margin = ARENA_HALF * 0.9
    player_pos[0] = clamp(player_pos[0], -margin, margin)
    player_pos[1] = clamp(player_pos[1], -margin, margin)

def update_enemies(dt):
    global life_limit

    for enemy in enemies:
        enemy["phase"] += 2.0 * dt
        dx = player_pos[0] - enemy["p"][0]
        dy = player_pos[1] - enemy["p"][1]
        dist = math.hypot(dx, dy) + 1e-6

        step = ENEMY_SPEED * dt
        enemy["p"][0] += (dx / dist) * step
        enemy["p"][1] += (dy / dist) * step

        if dist < enemy["r"] + 15.0:
            life_limit -= 1
            enemy["p"] = spawn_enemy_pos()

def update_bullets(dt):
    global miss, score

    remove_indices = []
    for i, bullet in enumerate(bullets):
        bullet["p"][0] += bullet["d"][0] * BULLET_SPEED * dt
        bullet["p"][1] += bullet["d"][1] * BULLET_SPEED * dt

        if abs(bullet["p"][0]) > ARENA_HALF or abs(bullet["p"][1]) > ARENA_HALF:
            miss += 1
            remove_indices.append(i)
            continue

        for enemy in enemies:
            radius = enemy["r"] * (1.0 + 0.15 * math.sin(enemy["phase"]))
            if xy_distance(bullet["p"], enemy["p"]) < radius + 7.0:
                score += 1
                enemy["p"] = spawn_enemy_pos()
                remove_indices.append(i)
                break

    for i in sorted(set(remove_indices), reverse=True):
        del bullets[i]

def update_cheat_mode(dt):
    global rotation_angle, cheat_fire_cooldown

    if not cheat_mode:
        return

    rotation_angle += CHEAT_ROTATE_SPEED * (dt * 60.0)
    if rotation_angle >= 360.0:
        rotation_angle -= 360.0

    if not enemies:
        return

    nearest = min(enemies, key=lambda e: math.hypot(e["p"][0] - player_pos[0], e["p"][1] - player_pos[1]))
    dx = nearest["p"][0] - player_pos[0]
    dy = nearest["p"][1] - player_pos[1]
    target_angle = math.degrees(math.atan2(dy, dx))

    angle_diff = (target_angle - rotation_angle + 360.0) % 360.0
    if angle_diff > 180.0:
        angle_diff -= 360.0

    if abs(angle_diff) < CHEAT_ANGLE_THRESHOLD and cheat_fire_cooldown <= 0.0:
        fire(nearest["p"])
        cheat_fire_cooldown = CHEAT_FIRE_INTERVAL

def camera_rig():
    if fps:
        head_x = player_pos[0]
        head_y = player_pos[1]
        head_z = player_pos[2] + HEAD_Z

        if cheat_mode and not auto_gun_follow:
            center_x = head_x
            center_y = head_y - 100.0
            center_z = head_z
        else:
            yaw_rad = math.radians(rotation_angle)
            center_x = head_x - math.cos(yaw_rad) * 100.0
            center_y = head_y - math.sin(yaw_rad) * 100.0
            center_z = head_z

        return [head_x, head_y, head_z], [center_x, center_y, center_z], [0, 0, 1]

    cam_x = math.cos(THIRD_ORBIT) * THIRD_CAM_R
    cam_y = math.sin(THIRD_ORBIT) * THIRD_CAM_R
    return [cam_x, cam_y, THIRD_CAM_Z], [0, 0, 0], [0, 0, 1]

def apply_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(field_view, aspect, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    eye, center, up = camera_rig()
    gluLookAt(eye[0], eye[1], eye[2], center[0], center[1], center[2], up[0], up[1], up[2])


def draw_scene():
    draw_arena()
    for bullet in bullets:
        draw_bullet(bullet)
    for enemy in enemies:
        draw_enemy(enemy)
    draw_player()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_w, window_h)
    apply_camera()
    draw_scene()
    if not game_over:
        draw_text(10, 770, f"Player Life Remaining: {life_limit}")
        draw_text(10, 745, f"Game Score: {score}")
        draw_text(10, 720, f"Player Bullet Missed: {miss}")
    else:
        draw_text(10, 770, f"Game is Over. Your Score is {score}.")
        draw_text(10, 745, "Press R to Restart.")

    glutSwapBuffers()

def key_down(key, _x, _y):
    global move_forward, move_back, turn_left, turn_right
    global cheat_mode, auto_gun_follow, cheat_fire_cooldown
    key = key.lower()
    if key == b"w":
        move_forward = True
    elif key == b"s":
        move_back = True
    elif key == b"a":
        turn_left = True
    elif key == b"d":
        turn_right = True
    elif key == b"c":
        cheat_mode = not cheat_mode
        if not cheat_mode:
            auto_gun_follow = False
            cheat_fire_cooldown = 0.0
    elif key == b"v" and cheat_mode:
        auto_gun_follow = not auto_gun_follow
    elif key == b"r":
        reset_game()

def key_up(key, _x, _y):
    global move_forward, move_back, turn_left, turn_right
    key = key.lower()
    if key == b"w":
        move_forward = False
    elif key == b"s":
        move_back = False
    elif key == b"a":
        turn_left = False
    elif key == b"d":
        turn_right = False

def special_key(key, _x, _y):
    global THIRD_CAM_Z, THIRD_ORBIT
    if key == GLUT_KEY_UP:
        THIRD_CAM_Z += 10.0
    elif key == GLUT_KEY_DOWN:
        THIRD_CAM_Z -= 10.0
    elif key == GLUT_KEY_LEFT:
        THIRD_ORBIT -= 0.02
    elif key == GLUT_KEY_RIGHT:
        THIRD_ORBIT += 0.02

def mouse(button, state, _x, _y):
    global fps
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fps = not fps

def idle():
    global last_tick, game_over, cheat_fire_cooldown
    now = time.perf_counter()
    if last_tick is None:
        last_tick = now
    dt = now - last_tick
    last_tick = now

    cheat_fire_cooldown = max(0.0, cheat_fire_cooldown - dt)

    if not game_over == True:
        update_player(dt)
        update_enemies(dt)
        update_bullets(dt)
        update_cheat_mode(dt)
        if life_limit <= 0 or miss >= MISS_LIMIT:
            game_over = True

    glutPostRedisplay()

def boot():
    glEnable(GL_DEPTH_TEST)
    glClearColor(*background, 1.0)
    reset_game()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_w, window_h)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy")
    boot()
    glutDisplayFunc(display)
    glutKeyboardFunc(key_down)
    glutKeyboardUpFunc(key_up)
    glutSpecialFunc(special_key)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
