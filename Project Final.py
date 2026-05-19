import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
class GameState:
    pass

config = GameState()

# State Constants
config.STATE_MENU     = 0
config.STATE_RACE     = 1
config.STATE_FREE_ROAM = 2
config.STATE_PAUSED   = 3
config.current_state  = config.STATE_MENU

# Menu & Settings
config.current_menu_selection = 0
config.setting_laps        = 3
config.setting_opponents   = 2
config.setting_difficulty  = "Normal"
config.setting_collisions  = True
config.setting_sensitivity = 2.0

def get_menu_options():
    return [
        "Start Race",
        "Free Roam",
        f"Laps: {config.setting_laps}",
        f"Difficulty: {config.setting_difficulty}",
        f"Collisions: {'ON' if config.setting_collisions else 'OFF'}",
        f"Sensitivity: {round(config.setting_sensitivity, 1)}"
    ]

# Camera Configuration
config.CAM_CHASE        = 0
config.CAM_HOOD         = 1
config.current_camera   = config.CAM_CHASE
config.cam_height_offset = 50.0
config.cam_swing_angle  = 0.0

# Physics & Player Car
config.MAX_SPEED      = 20.0
config.FRICTION       = 0.96          # applied EVERY frame -- was missing before!
config.THRUST         = 0.45
config.BRAKE_FORCE    = 0.40
config.MAX_WHEEL_ANGLE = 30.0

config.car_pos           = [0.0, 0.0, 0.0]
config.car_velocity      = [0.0, 0.0, 0.0]
config.car_facing_angle  = 0.0          # degrees, 0 = moving along +Z axis
config.current_wheel_angle = 0.0

config.keys_pressed = {b'w': False, b's': False, b'a': False, b'd': False}

# Race Progress
config.current_lap      = 1
config.race_start_time  = 0.0
config.current_race_time = 0.0
config.race_finished    = False
config.score            = 0            # distance-based score for endless mode
config.player_waypoint  = 0

# AI Opponents
config.ai_cars = []

def init_ai(num_opponents, difficulty):
    config.ai_cars = []
    num_opponents = 5 # Force exactly 2 AI opponents for the race (total 3 cars)
    
    # Calculate player's TRUE top speed due to friction equilibrium
    # Formula: terminal_velocity = thrust / (1 - friction)
    player_true_top_speed = config.THRUST / (1.0 - config.FRICTION)

    if difficulty == "Easy":
        # Roughly 84% of player's actual top speed
        speed_min = player_true_top_speed * 0.82
        speed_max = player_true_top_speed * 0.84
    elif difficulty == "Hard":
        # Exact same top speed as player
        speed_min = player_true_top_speed * 0.98
        speed_max = player_true_top_speed * 1.00
    else: # Normal
        # Roughly 89-92% of player's actual top speed
        speed_min = player_true_top_speed * 0.89
        speed_max = player_true_top_speed * 0.92

    # Ensure AI acceleration is much lower than player acceleration 
    # (Player thrust is 0.25, we give AI 0.03 so you can easily catch up)
    ai_acceleration = 0.03

    # Place them behind the player at the start line
    lanes = [-LANE_OFFSET, LANE_OFFSET] 
    for i in range(num_opponents):
        lane = lanes[i % 2]
        config.ai_cars.append({
            "pos": [lane, 0.0, -40.0],   # Start 40 units behind the player
            "max_speed": random.uniform(speed_min, speed_max),
            "accel": ai_acceleration,    # New variable for slower acceleration
            "lane": lane,
            "lane_change_timer": random.uniform(3.0, 7.0),
            "facing_angle": 0.0,
            "velocity_z": 0.0
        })
# ==========================================
# 2. ENDLESS HIGHWAY TRACK & ENVIRONMENT
# ==========================================

ROAD_WIDTH    = 120.0      # total tarmac width
LANE_OFFSET   = 35.0       # distance from centre to lane centre
ROAD_HALF     = ROAD_WIDTH / 2.0
ROAD_SEGMENT  = 200.0      # length of each visible road chunk
NUM_SEGMENTS  = 12         # how many chunks rendered ahead+behind

# Pre-built environment objects (generated once, then scrolled)
env_buildings = []   # list of (x, z, w, h, d, r, g, b)
env_trees     = []   # list of (x, z, r, g, b)
# Fix the generator (was using g_val before assigned)
def generate_env_objects():
    global env_buildings, env_trees
    env_buildings = []
    env_trees     = []

    ENV_SPAN = NUM_SEGMENTS * ROAD_SEGMENT

    rng = random.Random(42)
    for _ in range(80):
        side = rng.choice([-1, 1])
        x    = side * (ROAD_HALF + rng.uniform(20, 130))
        z    = rng.uniform(0, ENV_SPAN)
        w    = rng.uniform(18, 45)
        h    = rng.uniform(30, 100)
        d    = rng.uniform(18, 45)
        r    = rng.uniform(0.3, 1.0)
        g    = rng.uniform(0.3, 1.0)
        b_   = rng.uniform(0.3, 1.0)
        env_buildings.append((x, z, w, h, d, r, g, b_))

    for _ in range(120):
        side = rng.choice([-1, 1])
        x    = side * (ROAD_HALF + rng.uniform(8, 180))
        z    = rng.uniform(0, ENV_SPAN)
        r    = rng.uniform(0.0, 0.35)
        g    = rng.uniform(0.5, 0.9)
        b_   = rng.uniform(0.0, 0.25)
        env_trees.append((x, z, r, g, b_))


def draw_ground_plane():
    GROUND_HALF = 800.0
    ROAD_Z_NEAR = config.car_pos[2] - 400.0
    ROAD_Z_FAR  = config.car_pos[2] + 800.0
    is_night = getattr(config, 'setting_time_of_day', 'Day') == "Night"

    grass_color = (0.05, 0.2, 0.08) if is_night else (0.18, 0.55, 0.18)

    glColor3f(*grass_color)
    glBegin(GL_QUADS)
    glVertex3f(-GROUND_HALF, 0.0, ROAD_Z_NEAR)
    glVertex3f(-ROAD_HALF,   0.0, ROAD_Z_NEAR)
    glVertex3f(-ROAD_HALF,   0.0, ROAD_Z_FAR)
    glVertex3f(-GROUND_HALF, 0.0, ROAD_Z_FAR)
    glEnd()

    glColor3f(*grass_color)
    glBegin(GL_QUADS)
    glVertex3f(ROAD_HALF,   0.0, ROAD_Z_NEAR)
    glVertex3f(GROUND_HALF, 0.0, ROAD_Z_NEAR)
    glVertex3f(GROUND_HALF, 0.0, ROAD_Z_FAR)
    glVertex3f(ROAD_HALF,   0.0, ROAD_Z_FAR)
    glEnd()


def draw_road():
    pz        = config.car_pos[2]
    seg_start = math.floor(pz / ROAD_SEGMENT) -2
    white_w   = 3.0
    dash_len  = 20.0
    gap_len   = 20.0
    period    = dash_len + gap_len
    is_night  = getattr(config, 'setting_time_of_day', 'Day') == "Night"

    tarmac_color = (0.1, 0.1, 0.12) if is_night else (0.22, 0.22, 0.22)
    kerb_color   = (0.4, 0.4, 0.45) if is_night else (0.95, 0.95, 0.95)
    center_color = (0.6, 0.6, 0.0) if is_night else (1.0, 1.0, 0.0)
    dash_color   = (0.4, 0.4, 0.45) if is_night else (0.9, 0.9, 0.9)

    for s in range(seg_start, seg_start + NUM_SEGMENTS):
        z0 = s * ROAD_SEGMENT
        z1 = z0 + ROAD_SEGMENT

        glColor3f(*tarmac_color)
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_HALF, 0.01, z0)
        glVertex3f( ROAD_HALF, 0.01, z0)
        glVertex3f( ROAD_HALF, 0.01, z1)
        glVertex3f(-ROAD_HALF, 0.01, z1)
        glEnd()

        glColor3f(*kerb_color)
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_HALF,       0.02, z0)
        glVertex3f(-ROAD_HALF + 4.0, 0.02, z0)
        glVertex3f(-ROAD_HALF + 4.0, 0.02, z1)
        glVertex3f(-ROAD_HALF,       0.02, z1)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(ROAD_HALF - 4.0, 0.02, z0)
        glVertex3f(ROAD_HALF,       0.02, z0)
        glVertex3f(ROAD_HALF,       0.02, z1)
        glVertex3f(ROAD_HALF - 4.0, 0.02, z1)
        glEnd()

    first_dash = math.floor(pz / period) -5
    for d in range(first_dash, first_dash + 60):
        dz0 = d * period
        dz1 = dz0 + dash_len
        for lane_x in [0.0, -LANE_OFFSET, LANE_OFFSET]:
            glColor3f(*center_color) if lane_x == 0.0 else glColor3f(*dash_color)
            glBegin(GL_QUADS)
            glVertex3f(lane_x - white_w, 0.03, dz0)
            glVertex3f(lane_x + white_w, 0.03, dz0)
            glVertex3f(lane_x + white_w, 0.03, dz1)
            glVertex3f(lane_x - white_w, 0.03, dz1)
            glEnd()


def draw_environment():
    ENV_SPAN = NUM_SEGMENTS * ROAD_SEGMENT
    pz       = config.car_pos[2]
    base_offset = math.floor(pz / ENV_SPAN) * ENV_SPAN
    is_night = getattr(config, 'setting_time_of_day', 'Day') == "Night"

    # --- NEW: 3D Sun and Moon ---
    # Lowered the Y value to 300 so it actually fits inside the camera's downward tilt!
    glPushMatrix()
    celestial_z = pz + 3200.0  
    glTranslatef(300.0, 300.0, celestial_z) 
    if is_night:
        glColor3f(0.9, 0.9, 0.8) # Moon
        gluSphere(gluNewQuadric(), 150.0, 20, 20)
    else:
        glColor3f(1.0, 0.9, 0.2) # Sun
        gluSphere(gluNewQuadric(), 150.0, 20, 20)
    glPopMatrix()
    # ----------------------------

    for (bx, bz, bw, bh, bd, r, g, b) in env_buildings:
        world_z = bz + base_offset
        if world_z < pz - 300 or world_z > pz + 700:
            world_z += ENV_SPAN if world_z < pz - 300 else -ENV_SPAN
        if abs(world_z - pz) > 750:
            continue

        glPushMatrix()
        glTranslatef(bx, 0.0, world_z)
        
        # Apply night darkening to building base color
        if is_night:
            glColor3f(r * 0.2, g * 0.2, b * 0.3)
        else:
            glColor3f(r, g, b)
            
        glTranslatef(0.0, bh / 2.0, 0.0)
        glScalef(bw, bh, bd)
        glutSolidCube(1.0)
        glPopMatrix()

        # Windows (Moved to the -Z face so the oncoming player sees them!)
        glPushMatrix()
        glTranslatef(bx, bh * 0.5, world_z - bd * 0.52) 
        
        if is_night:
            glColor3f(1.0, 0.9, 0.2) # Bright glowing yellow windows
        else:
            glColor3f(0.3, 0.5, 0.6) # Darker daytime glass

        rows = max(1, int(bh / 20))
        cols = max(1, int(bw / 12))
        for row in range(rows):
            for col in range(cols):
                wy = -bh * 0.4 + row * (bh * 0.8 / max(rows, 1))
                wx =  -bw * 0.35 + col * (bw * 0.7 / max(cols, 1))
                glPushMatrix()
                glTranslatef(wx, wy, 0)
                glScalef(4.0, 4.0, 0.5)
                glutSolidCube(1.0)
                glPopMatrix()
        glPopMatrix()

    for (tx, tz, r, g, b) in env_trees:
        world_z = tz + base_offset
        if world_z < pz - 300 or world_z > pz + 700:
            world_z += ENV_SPAN if world_z < pz - 300 else -ENV_SPAN
        if abs(world_z - pz) > 750:
            continue

        # Trunk
        glPushMatrix()
        glTranslatef(tx, 0.0, world_z)
        if is_night:
            glColor3f(0.15, 0.08, 0.02)
        else:
            glColor3f(0.45, 0.27, 0.07)
        gluCylinder(gluNewQuadric(), 2.5, 1.5, 14.0, 8, 4)
        glPopMatrix()

        # Foliage
        glPushMatrix()
        glTranslatef(tx, 18.0, world_z)
        if is_night:
            glColor3f(r * 0.3, g * 0.3, b * 0.4)
        else:
            glColor3f(r, g, b)
        gluSphere(gluNewQuadric(), 12.0, 8, 8)
        glPopMatrix()


def draw_sky():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(-1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    is_night = getattr(config, 'setting_time_of_day', 'Day') == "Night"

    if is_night:
        # Night sky gradient
        glBegin(GL_QUADS)
        glColor3f(0.02, 0.02, 0.08)   
        glVertex2f(-1,  1)
        glVertex2f( 1,  1)
        glColor3f(0.1, 0.1, 0.2)   
        glVertex2f( 1, -1)
        glVertex2f(-1, -1)
        glEnd()
    else:
        # Day sky gradient
        glBegin(GL_QUADS)
        glColor3f(0.1, 0.4, 0.8)   
        glVertex2f(-1,  1)
        glVertex2f( 1,  1)
        glColor3f(0.6, 0.8, 1.0)   
        glVertex2f( 1, -1)
        glVertex2f(-1, -1)
        glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_ai():
    for ai in config.ai_cars:
        ai["lane_change_timer"] -= 0.016
        if ai["lane_change_timer"] <= 0:
            ai["lane"] = random.choice([-LANE_OFFSET, 0.0, LANE_OFFSET])
            ai["lane_change_timer"] = random.uniform(3.0, 7.0)

        # Smoothly approach target lane X
        target_x = ai["lane"]
        dx = target_x - ai["pos"][0]
        ai["pos"][0] += dx * 0.04

        # Accelerate toward max speed using their specific, slower acceleration
        ai["velocity_z"] = min(ai["velocity_z"] + ai["accel"], ai["max_speed"])
        ai["pos"][2] += ai["velocity_z"]
        ai["facing_angle"] = 0.0   # AI always faces forward (+Z)

# ==========================================
# 4. CAMERA
# ==========================================
def apply_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(80, 1.25, 0.5, 4000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    rad_facing = math.radians(config.car_facing_angle)
    facing_dx  = math.sin(rad_facing)
    facing_dz  = math.cos(rad_facing)

    if config.current_camera == config.CAM_CHASE:
        cam_dist   = 80.0
        swing_rad  = math.radians(config.cam_swing_angle)
        cam_x = config.car_pos[0] - math.sin(rad_facing + swing_rad) * cam_dist
        cam_z = config.car_pos[2] - math.cos(rad_facing + swing_rad) * cam_dist
        cam_y = config.car_pos[1] + config.cam_height_offset
        gluLookAt(cam_x, cam_y, cam_z,
                  config.car_pos[0], config.car_pos[1] + 5, config.car_pos[2],
                  0, 1, 0)
    else:  # Hood cam
        cam_x = config.car_pos[0] + facing_dx * 10.0
        cam_y = config.car_pos[1] + 15.0
        cam_z = config.car_pos[2] + facing_dz * 10.0
        gluLookAt(cam_x, cam_y, cam_z,
                  cam_x + facing_dx * 200.0, cam_y, cam_z + facing_dz * 200.0, 0, 1, 0)


# ==========================================
# 5. CAR MODEL
# ==========================================
def draw_car(is_player=True, x=0, y=0, z=0, angle=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 1, 0)

    if is_player:
        roll  = config.current_wheel_angle * 0.3
        speed = math.sqrt(config.car_velocity[0]**2 + config.car_velocity[2]**2)
        pitch = -speed * 0.5 if config.keys_pressed[b'w'] else (speed * 0.3 if config.keys_pressed[b's'] else 0)
        glRotatef(pitch, 1, 0, 0)
        glRotatef(roll,  0, 0, 1)

    # --- Body (Chassis) ---
    glColor3f(0.85, 0.1, 0.1) if is_player else glColor3f(0.1, 0.2, 0.85)
    glPushMatrix()
    glTranslatef(0, 7, 0)
    glScalef(1.1, 0.35, 2.2) 
    glutSolidCube(20)
    glPopMatrix()

    # --- Cabin (Roof) ---
    glColor3f(0.6, 0.05, 0.05) if is_player else glColor3f(0.05, 0.1, 0.6)
    glPushMatrix()
    glTranslatef(0, 14, -2)
    glScalef(0.8, 0.35, 1.0)
    glutSolidCube(20)
    glPopMatrix()
    
    # --- Glass (Windshields & Windows) ---
    glColor3f(0.5, 0.8, 0.9) 
    
    # Windshield (Front)
    glPushMatrix()
    glTranslatef(0, 14, 8) 
    glRotatef(20, 1, 0, 0) 
    glScalef(0.78, 0.32, 0.05)
    glutSolidCube(20)
    glPopMatrix()
    
    # Rear Window
    glPushMatrix()
    glTranslatef(0, 14, -12) 
    glRotatef(-15, 1, 0, 0)
    glScalef(0.78, 0.32, 0.05)
    glutSolidCube(20)
    glPopMatrix()
    
    # Side Windows 
    glPushMatrix()
    glTranslatef(-8.1, 14, -2) 
    glScalef(0.05, 0.32, 0.95)
    glutSolidCube(20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(8.1, 14, -2)
    glScalef(0.05, 0.32, 0.95)
    glutSolidCube(20)
    glPopMatrix()

    # --- Wheels (Lowered and tucked to fix the top-view glitch!) ---
    wheel_positions = [(-11.0, 3.5, 12), (11.0, 3.5, 12), (-11.0, 3.5, -12), (11.0, 3.5, -12)]
    for i, (wx, wy, wz) in enumerate(wheel_positions):
        glPushMatrix()
        glTranslatef(wx, wy, wz)
        if is_player and i < 2:          
            glRotatef(config.current_wheel_angle, 0, 1, 0)
        
        # 1. Tire Tread (Cylinder)
        glColor3f(0.1, 0.1, 0.1) 
        glPushMatrix()
        glRotatef(90, 0, 1, 0)
        glTranslatef(0, 0, -2.5) 
        gluCylinder(gluNewQuadric(), 3.5, 3.5, 5.0, 12, 4)
        glPopMatrix()

        # 2. Tire Wall (Flattened Sphere)
        glColor3f(0.15, 0.15, 0.15)
        glPushMatrix()
        glScalef(0.4, 1.0, 1.0) 
        gluSphere(gluNewQuadric(), 3.4, 12, 12)
        glPopMatrix()

        # 3. Hubcap 
        glColor3f(0.7, 0.7, 0.7)
        glPushMatrix()
        side_dir = -1 if wx < 0 else 1
        glTranslatef(side_dir * 2.6, 0, 0)
        glScalef(0.3, 1.0, 1.0)
        gluSphere(gluNewQuadric(), 1.8, 10, 8)
        glPopMatrix()

        glPopMatrix()

    glPopMatrix()


# ==========================================
# 6. PHYSICS
# ==========================================
def update_physics():
    if config.race_finished:
        return

    config.TURN_SPEED = config.setting_sensitivity

    # --- Steering ---
    target_wheel = 0.0
    if config.keys_pressed[b'a']:
        target_wheel =  config.MAX_WHEEL_ANGLE
    elif config.keys_pressed[b'd']:
        target_wheel = -config.MAX_WHEEL_ANGLE

    step = config.TURN_SPEED
    if config.current_wheel_angle < target_wheel:
        config.current_wheel_angle = min(config.current_wheel_angle + step, target_wheel)
    elif config.current_wheel_angle > target_wheel:
        config.current_wheel_angle = max(config.current_wheel_angle - step, target_wheel)

    # --- Thrust / Brake ---
    rad_facing  = math.radians(config.car_facing_angle)
    facing_dx   = math.sin(rad_facing)
    facing_dz   = math.cos(rad_facing)
    fwd_vel     = (config.car_velocity[0] * facing_dx +
                   config.car_velocity[2] * facing_dz)

    if config.keys_pressed[b'w']:
        if fwd_vel < -0.1:
            config.car_velocity[0] += facing_dx * config.BRAKE_FORCE * 2.0
            config.car_velocity[2] += facing_dz * config.BRAKE_FORCE * 2.0
        else:
            config.car_velocity[0] += facing_dx * config.THRUST
            config.car_velocity[2] += facing_dz * config.THRUST

    if config.keys_pressed[b's']:
        if fwd_vel > 0.1:
            config.car_velocity[0] -= facing_dx * config.BRAKE_FORCE * 2.0
            config.car_velocity[2] -= facing_dz * config.BRAKE_FORCE * 2.0
        else:
            config.car_velocity[0] -= facing_dx * config.THRUST * 0.5
            config.car_velocity[2] -= facing_dz * config.THRUST * 0.5

    # --- FRICTION ---
    config.car_velocity[0] *= config.FRICTION
    config.car_velocity[2] *= config.FRICTION

    # --- Clamp to max speed ---
    speed = math.sqrt(config.car_velocity[0]**2 + config.car_velocity[2]**2)
    if speed > config.MAX_SPEED:
        ratio = config.MAX_SPEED / speed
        config.car_velocity[0] *= ratio
        config.car_velocity[2] *= ratio

    # --- Turning (speed-dependent) ---
    if speed > 0.2:
        # NEW: Check if reversing to invert the steering angle naturally
        direction_multiplier = 1.0 if fwd_vel >= 0 else -1.0
        turn_factor = (speed / config.MAX_SPEED) * 0.18 * direction_multiplier
        
        config.car_facing_angle += config.current_wheel_angle * turn_factor
        
        # Slight speed reduction when turning (scrubbing speed realistically)
        if abs(config.current_wheel_angle) > 5.0:
            config.car_velocity[0] *= 0.99
            config.car_velocity[2] *= 0.99

    # --- Road boundary clamp (keep on road) ---
    ROAD_HALF = 60.0
    config.car_pos[0] = max(-ROAD_HALF + 12, min(ROAD_HALF - 12, config.car_pos[0]))

    # --- Move car ---
    config.car_pos[0] += config.car_velocity[0]
    config.car_pos[2] += config.car_velocity[2]

    # --- Score (distance driven) ---
    config.score = max(config.score, int(config.car_pos[2] / 10))

def check_collisions_and_laps():
    if config.race_finished:
        return

    if config.setting_collisions:
        hit_radius = 18.0
        for ai in config.ai_cars:
            dx = config.car_pos[0] - ai["pos"][0]
            dz = config.car_pos[2] - ai["pos"][2]
            dist = math.sqrt(dx**2 + dz**2)
            if dist < hit_radius and dist > 0.01:
                # Slight realistic speed decrease instead of massive stop
                config.car_velocity[0] *= 0.85 
                config.car_velocity[2] *= 0.85
                config.car_pos[0] += (dx / dist) * 3.0
                config.car_pos[2] += (dz / dist) * 3.0

    # Lap / distance checkpoint for Race mode
    if config.current_state == config.STATE_RACE:
        lap_distance = 3000.0
        
        # Calculate current lap (Start at lap 1)
        config.current_lap = int(config.car_pos[2] / lap_distance) + 1
        
        # Check if we passed the final finish line
        if config.current_lap > config.setting_laps and not config.race_finished:
            config.race_finished = True
            config.current_lap = config.setting_laps # Lock HUD display to max laps
            
            # --- NEW: Lock the final position ---
            # This ensures if the AI drives past your parked car after the race, 
            # your placement text doesn't change!
            all_z_positions = [config.car_pos[2]] + [ai["pos"][2] for ai in config.ai_cars]
            all_z_positions.sort(reverse=True)
            config.final_position = all_z_positions.index(config.car_pos[2]) + 1


# ==========================================
# 7. TEXT & UI
# ==========================================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_time_select_menu():
    # Background
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glBegin(GL_QUADS)
    glColor3f(0.05, 0.05, 0.15)
    glVertex2f(0, 800)
    glVertex2f(1000, 800)
    glColor3f(0.10, 0.10, 0.35)
    glVertex2f(1000, 0)
    glVertex2f(0, 0)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    draw_text(370, 550, "SELECT TIME OF DAY", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(360, 500, "W/S = navigate   ENTER = select")

    opts  = ["Day Mode", "Night Mode"]
    start_y  = 400
    for i, option in enumerate(opts):
        ypos = start_y - i * 50
        if i == getattr(config, 'current_time_selection', 0):
            draw_text(410, ypos, f">  {option}  <")
        else:
            draw_text(440, ypos, option)


def draw_main_menu():
    # Background
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Sky gradient
    glBegin(GL_QUADS)
    glColor3f(0.05, 0.05, 0.15)
    glVertex2f(0, 800)
    glVertex2f(1000, 800)
    glColor3f(0.10, 0.10, 0.35)
    glVertex2f(1000, 0)
    glVertex2f(0, 0)
    glEnd()

    # Road strip at bottom
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(1000, 0)
    glVertex2f(1000, 120); glVertex2f(0, 120)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    draw_text(360, 680, "VECTOR VELOCITY", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(310, 640, "Endless Highway Racing  |  CSE 423 Group 01")
    draw_text(290, 600, "W/S = navigate menu   A/D = change value   ENTER = select")

    options  = get_menu_options()
    start_y  = 530
    for i, option in enumerate(options):
        ypos = start_y - i * 42
        if i == config.current_menu_selection:
            draw_text(370, ypos, f">  {option}  <")
            if i >= 2:
                draw_text(660, ypos, "[A / D]")
        else:
            draw_text(400, ypos, option)

    draw_text(300, 150, "In-game controls:")
    draw_text(300, 120, "W/S = Gas/Brake   A/D = Steer   P = Pause   RMB = Toggle Camera")
    draw_text(300, 90,  "Arrow Keys = Camera angle/height   M = Main Menu (when paused/finished)")


def draw_pause_menu():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Solid dark blue background instead of transparent to avoid needing GL_BLEND
    glColor3f(0.05, 0.05, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(350, 300)
    glVertex2f(650, 300)
    glVertex2f(650, 500)
    glVertex2f(350, 500)
    glEnd()
    
    draw_text(445, 460, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(390, 410, "Press  'P'  to Resume")
    draw_text(390, 370, "Press  'M'  for Main Menu")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    speed_val = math.sqrt(config.car_velocity[0]**2 + config.car_velocity[2]**2)
    speed_kmh = int(speed_val * 18)   # rough km/h scale
    draw_text(20, 40, f"Speed: {speed_kmh} km/h")
    draw_text(20, 70, f"Score: {config.score} m")

    cam_label = "Chase Cam" if config.current_camera == config.CAM_CHASE else "Hood Cam"
    draw_text(840, 40, cam_label)

    if config.current_state == config.STATE_RACE:
        
        # --- POSITION CALCULATION ---
        # Sort all cars by their Z coordinate (highest Z is 1st place)
        all_z_positions = [config.car_pos[2]] + [ai["pos"][2] for ai in config.ai_cars]
        all_z_positions.sort(reverse=True)
        player_pos = all_z_positions.index(config.car_pos[2]) + 1
        
        # --- COUNTDOWN DISPLAY ---
        elapsed_total = time.time() - config.race_start_time
        if elapsed_total < 3.0:
            countdown_num = 3 - int(elapsed_total)
            draw_text(480, 450, str(countdown_num), GLUT_BITMAP_TIMES_ROMAN_24)
        elif elapsed_total < 4.0:
            draw_text(470, 450, "GO!", GLUT_BITMAP_TIMES_ROMAN_24)

        elapsed = f"{config.current_race_time:.1f}s" if config.current_race_time > 0 else "0.0s"
        
        # --- LAP & POS DISPLAY ---
        draw_text(840, 780, f"Pos: {player_pos} / 3")
        draw_text(840, 750, f"Lap: {config.current_lap} / {config.setting_laps}")
        draw_text(840, 720, f"Time: {elapsed}")

        if config.race_finished:
            # Use the locked final position so it doesn't change after you stop
            final_pos = getattr(config, 'final_position', player_pos)
            
            # --- NEW: Custom End Messages ---
            if final_pos == 1:
                draw_text(300, 500, "Congratulations, You're the winner", GLUT_BITMAP_TIMES_ROMAN_24)
            elif final_pos == 2:
                draw_text(360, 500, "Great, You're Runnerup", GLUT_BITMAP_TIMES_ROMAN_24)
            else:
                draw_text(360, 500, "You looser, Try again.", GLUT_BITMAP_TIMES_ROMAN_24)
                
            draw_text(390, 455, f"Final Time: {config.current_race_time:.1f}s")
            draw_text(360, 415, "Press 'M' for Main Menu")

    elif config.current_state == config.STATE_FREE_ROAM:
        draw_text(830, 750, "FREE ROAM")

# ==========================================
# 8. MAIN GAME LOOP
# ==========================================
def reset_race():
    config.car_pos           = [0.0, 0.0, 0.0]
    config.car_velocity      = [0.0, 0.0, 0.0]
    config.car_facing_angle  = 0.0
    config.current_wheel_angle = 0.0
    config.current_lap       = 1
    config.player_waypoint   = 0
    config.race_finished     = False
    config.score             = 0
    config.race_start_time   = time.time()
    config.cam_swing_angle   = 0.0
    config.cam_height_offset = 50.0
    config.current_camera    = config.CAM_CHASE


def keyboardListener(key, x, y):
    # Safely initialize new Day/Night state variables if they don't exist
    if not hasattr(config, 'STATE_TIME_SELECT'):
        config.STATE_TIME_SELECT = 4
        config.current_time_selection = 0
        config.pending_game_state = config.STATE_RACE
        config.setting_time_of_day = "Day"

    key_lower = key.lower()

    if config.current_state == config.STATE_MENU:
        opts = get_menu_options()
        if key_lower == b'w':
            config.current_menu_selection = max(0, config.current_menu_selection - 1)
        elif key_lower == b's':
            config.current_menu_selection = min(len(opts) - 1, config.current_menu_selection + 1)
        elif key_lower in (b'a', b'd'):
            direction = -1 if key_lower == b'a' else 1
            sel = config.current_menu_selection
            
            if sel == 2:
                config.setting_laps = max(1, min(10, config.setting_laps + direction))
            elif sel == 3:
                diffs = ["Easy", "Normal", "Hard"]
                idx = diffs.index(config.setting_difficulty)
                config.setting_difficulty = diffs[(idx + direction) % 3]
            elif sel == 4:
                config.setting_collisions = not config.setting_collisions
            elif sel == 5:
                config.setting_sensitivity = max(1.0, min(4.0, config.setting_sensitivity + direction * 0.5))
        
        elif key == b'\r':
            # Instead of starting the game directly, go to Time Selection
            if config.current_menu_selection == 0:
                config.pending_game_state = config.STATE_RACE
                config.current_state = config.STATE_TIME_SELECT
                config.current_time_selection = 0
            elif config.current_menu_selection == 1:
                config.pending_game_state = config.STATE_FREE_ROAM
                config.current_state = config.STATE_TIME_SELECT
                config.current_time_selection = 0

    elif config.current_state == config.STATE_TIME_SELECT:
        if key_lower == b'w':
            config.current_time_selection = 0
        elif key_lower == b's':
            config.current_time_selection = 1
        elif key == b'\r':
            # Set the time of day and finalize the game launch
            config.setting_time_of_day = "Day" if config.current_time_selection == 0 else "Night"
            reset_race()
            config.current_state = config.pending_game_state
            if config.current_state == config.STATE_RACE:
                init_ai(config.setting_opponents, config.setting_difficulty)
            else:
                config.ai_cars = []

    elif config.current_state in [config.STATE_RACE, config.STATE_FREE_ROAM]:
        if key_lower in config.keys_pressed:
            config.keys_pressed[key_lower] = True
        if key_lower == b'p':
            config.current_state = config.STATE_PAUSED
        if config.race_finished and key_lower == b'm':
            config.current_state = config.STATE_MENU

    elif config.current_state == config.STATE_PAUSED:
        if key_lower == b'p':
            config.current_state = config.STATE_RACE
        elif key_lower == b'm':
            config.current_state = config.STATE_MENU

    glutPostRedisplay()


def keyboardUpListener(key, x, y):
    key_lower = key.lower()
    if key_lower in config.keys_pressed:
        config.keys_pressed[key_lower] = False


def specialKeyListener(key, x, y):
    if config.current_state in [config.STATE_RACE, config.STATE_FREE_ROAM]:
        if key == GLUT_KEY_UP:
            config.cam_height_offset += 3.0
        elif key == GLUT_KEY_DOWN:
            config.cam_height_offset = max(10.0, config.cam_height_offset - 3.0)
        elif key == GLUT_KEY_LEFT:
            config.cam_swing_angle += 3.0
        elif key == GLUT_KEY_RIGHT:
            config.cam_swing_angle -= 3.0
    glutPostRedisplay()


def mouseListener(button, state, x, y):
    if config.current_state in [config.STATE_RACE, config.STATE_FREE_ROAM]:
        if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            config.current_camera = (config.CAM_HOOD
                                     if config.current_camera == config.CAM_CHASE
                                     else config.CAM_CHASE)
    glutPostRedisplay()


def idle():
    if config.current_state in [config.STATE_RACE, config.STATE_FREE_ROAM]:
        elapsed_total = time.time() - config.race_start_time
        
        # --- COUNTDOWN LOGIC ---
        if config.current_state == config.STATE_RACE and elapsed_total < 3.0:
            config.current_race_time = 0.0 # Race timer doesn't start yet
            glutPostRedisplay()
            return # Freeze the game logic during countdown
            
        if not config.race_finished:
            if config.current_state == config.STATE_RACE:
                config.current_race_time = elapsed_total - 3.0 # Shift timer so it starts at 0
            else:
                config.current_race_time = elapsed_total
                
        update_physics()
        check_collisions_and_laps()
        update_ai()
        glutPostRedisplay()
def draw_lap_lines():
    lap_distance = 3000.0
    ROAD_HALF = 60.0 
    
    # Draw the start line and all lap finish lines
    for lap in range(config.setting_laps + 1):
        z_pos = lap * lap_distance
        
        # Only draw if it's close to the player to save rendering performance
        if abs(config.car_pos[2] - z_pos) < 1000:
            strip_width = 15.0
            
            # White base line
            glColor3f(1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glVertex3f(-ROAD_HALF, 0.04, z_pos)
            glVertex3f(ROAD_HALF, 0.04, z_pos)
            glVertex3f(ROAD_HALF, 0.04, z_pos + strip_width)
            glVertex3f(-ROAD_HALF, 0.04, z_pos + strip_width)
            glEnd()
            
            # Black checkered squares
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_QUADS)
            num_squares = 12
            sq_width = (ROAD_HALF * 2) / num_squares
            for i in range(num_squares):
                sx = -ROAD_HALF + i * sq_width
                if i % 2 == 0: # Front row squares
                    glVertex3f(sx, 0.05, z_pos)
                    glVertex3f(sx + sq_width, 0.05, z_pos)
                    glVertex3f(sx + sq_width, 0.05, z_pos + strip_width/2)
                    glVertex3f(sx, 0.05, z_pos + strip_width/2)
                else:          # Back row squares
                    glVertex3f(sx, 0.05, z_pos + strip_width/2)
                    glVertex3f(sx + sq_width, 0.05, z_pos + strip_width/2)
                    glVertex3f(sx + sq_width, 0.05, z_pos + strip_width)
                    glVertex3f(sx, 0.05, z_pos + strip_width)
            glEnd()

def showScreen():
    # Clear buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    STATE_TIME_SELECT = getattr(config, 'STATE_TIME_SELECT', 4)

    if config.current_state == config.STATE_MENU:
        draw_main_menu()
        
    elif config.current_state == STATE_TIME_SELECT:
        draw_time_select_menu()

    elif config.current_state in [config.STATE_RACE,
                                   config.STATE_FREE_ROAM,
                                   config.STATE_PAUSED]:
        
        # Draw sky first (without depth testing enabled yet)
        draw_sky()                     
        apply_camera()
        
        # --- THE ALLOWED EXCEPTION ---
        # Enabling Depth Test exactly as permitted to stop the see-through world bugs
        glEnable(GL_DEPTH_TEST)

        draw_ground_plane()
        draw_road()
        draw_lap_lines() 
        draw_environment()

        # Player car
        draw_car(True,
                 config.car_pos[0], config.car_pos[1], config.car_pos[2],
                 config.car_facing_angle)

        # AI cars
        for ai in config.ai_cars:
            draw_car(False,
                     ai["pos"][0], ai["pos"][1], ai["pos"][2],
                     ai["facing_angle"])

        # Disable Depth Test before 2D HUD so text draws perfectly on top
        glDisable(GL_DEPTH_TEST)

        # --- 2-D overlays ---
        if config.current_state == config.STATE_PAUSED:
            draw_pause_menu()
        else:
            draw_hud()

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Vector Velocity  |  CSE 423")

    generate_env_objects()

    glutDisplayFunc(showScreen)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)

    glutMainLoop()


if __name__ == "__main__":
    main()

