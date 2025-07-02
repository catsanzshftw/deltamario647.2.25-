# b3313_engine.py
from ursina import *
from ursina.shaders import lit_with_shadows_shader
import math
import random

# ----------- GAME SETUP -----------
app = Ursina()
window.title = 'B3313 1.0 - SPECIAL 64 EMULATOR'
window.fps_counter.enabled = True
window.exit_button.visible = False
window.borderless = False
window.fullscreen = False

# ----------- B3313 GAME STATE & ASSETS -----------
state = {
    'coins': 0,
    'stars': 0,
    'king_bobomb_throws': 0,
    'is_holding_king': False,
    'game_mode': 'splash',  # 'splash', 'menu', 'game'
    'current_floor': 0,
    'personalization_level': 0,
    'rooms_visited': [],
    'ai_watching': True,
}

# B3313 Ambient sounds
try:
    coin_sound = Audio('coin', loop=False, autoplay=False)
    stomp_sound = Audio('hit', loop=False, autoplay=False)
    star_sound = Audio('powerup', loop=False, autoplay=False)
    jump_sound = Audio('jump', loop=False, autoplay=False)
    ambient_hum = Audio('ambience', loop=True, autoplay=False, volume=0.3)
except:
    coin_sound = Audio('', loop=False, autoplay=False)
    stomp_sound = Audio('', loop=False, autoplay=False)
    star_sound = Audio('', loop=False, autoplay=False)
    jump_sound = Audio('', loop=False, autoplay=False)
    ambient_hum = Audio('', loop=False, autoplay=False)

# ----------- SPLASH SCREEN -----------
def show_splash_screen():
    """Show TEAM SPECIALEMU AGI Division splash"""
    splash_bg = Entity(model='cube', scale=(50, 50, 1), position=(0, 0, -5), color=color.black)
    
    # Glitchy text effect
    splash_text = Text(
        'TEAM SPECIALEMU AGI Division Presents',
        position=(0, 0.1),
        origin=(0, 0),
        scale=3,
        color=color.red
    )
    
    # Special 64 logo
    special_64_text = Text(
        'SPECIAL 64 EMULATOR v1.0',
        position=(0, -0.1),
        origin=(0, 0),
        scale=2,
        color=color.white
    )
    
    # Glitch effect
    def glitch_text():
        if random.random() < 0.3:
            splash_text.color = random.choice([color.red, color.white, color.black])
            splash_text.scale = 3 + random.uniform(-0.2, 0.2)
    
    Entity(update=glitch_text)
    
    # Transition to menu after 3 seconds
    invoke(lambda: transition_to_menu(splash_bg, splash_text, special_64_text), delay=3)

def transition_to_menu(*entities):
    for e in entities:
        destroy(e)
    state['game_mode'] = 'menu'
    setup_b3313_menu()

# ----------- B3313 MARIO HEAD MENU -----------
class B3313MarioHead(Entity):
    def __init__(self):
        super().__init__()
        self.original_position = Vec3(0, 0, 0)
        self.mouse_sensitivity = 2
        self.elasticity = 0.15
        self.max_stretch = 2
        self.is_being_grabbed = False
        self.grab_offset = Vec3()
        self.face_parts = {}
        self.glitch_timer = 0
        
        # Create Mario's head with B3313 corruptions
        self.setup_head()
        
        # B3313 style background
        self.create_b3313_background()
        
    def setup_head(self):
        """Create Mario's head with potential corruptions"""
        # Main head (sphere) - sometimes distorted
        head_color = color.peach if random.random() > 0.1 else color.black
        self.head = Entity(
            model='sphere', 
            color=head_color, 
            scale=3,
            position=(0, 0, 0),
            parent=self
        )
        
        # Hat - sometimes missing or wrong color
        hat_color = color.red if random.random() > 0.2 else color.black
        self.hat = Entity(
            model='sphere',
            color=hat_color,
            scale=(3.2, 1.5, 3.2),
            position=(0, 1.2, 0),
            parent=self,
            enabled=random.random() > 0.1
        )
        
        # Hat brim
        self.hat_brim = Entity(
            model='cylinder',
            color=hat_color,
            scale=(4, 0.2, 4),
            position=(0, 0.3, 0.5),
            rotation=(15, 0, 0),
            parent=self,
            enabled=self.hat.enabled
        )
        
        # M emblem - sometimes corrupted
        emblem_text = 'M' if random.random() > 0.3 else random.choice(['W', 'L', '?', '⬛'])
        self.m_emblem = Entity(
            model='cube',
            color=color.white,
            scale=(0.8, 0.8, 0.1),
            position=(0, 0.5, 1.4),
            parent=self,
            enabled=self.hat.enabled
        )
        
        # Eyes - sometimes asymmetric or missing
        self.left_eye = Entity(
            model='sphere',
            color=color.black if random.random() > 0.1 else color.red,
            scale=(0.3, 0.4, 0.3),
            position=(-0.6, 0.2, 1.2),
            parent=self,
            enabled=random.random() > 0.05
        )
        
        self.right_eye = Entity(
            model='sphere',
            color=color.black if random.random() > 0.1 else color.red,
            scale=(0.3, 0.4, 0.3),
            position=(0.6, 0.2, 1.2),
            parent=self,
            enabled=random.random() > 0.05
        )
        
        # Nose
        self.nose = Entity(
            model='sphere',
            color=color.peach,
            scale=(0.4, 0.3, 0.6),
            position=(0, -0.1, 1.3),
            parent=self
        )
        
        # Mustache - sometimes wrong
        self.mustache = Entity(
            model='cube',
            color=color.brown if random.random() > 0.2 else color.black,
            scale=(1.2, 0.15, 0.3),
            position=(0, -0.4, 1.1),
            parent=self,
            enabled=random.random() > 0.1
        )
        
        # Ears
        self.left_ear = Entity(
            model='sphere',
            color=color.peach,
            scale=(0.6, 0.8, 0.4),
            position=(-1.4, 0, 0.2),
            parent=self
        )
        
        self.right_ear = Entity(
            model='sphere',
            color=color.peach,
            scale=(0.6, 0.8, 0.4),
            position=(1.4, 0, 0.2),
            parent=self
        )
        
        # Store grabbable parts
        self.grabbable_parts = {
            'nose': self.nose,
            'left_ear': self.left_ear,
            'right_ear': self.right_ear,
            'head': self.head
        }
        
    def create_b3313_background(self):
        """Create B3313's unsettling background"""
        # Dark void with occasional geometry
        for i in range(30):
            entity_type = random.choice(['cube', 'sphere', 'cylinder'])
            void_entity = Entity(
                model=entity_type,
                color=color.black,
                scale=random.uniform(1, 5),
                position=(
                    random.uniform(-20, 20),
                    random.uniform(-15, 15),
                    random.uniform(-30, -10)
                )
            )
            # Slow rotation
            void_entity.animate('rotation', Vec3(360, 360, 360), duration=random.uniform(10, 30), loop=True)
        
        # Corrupted stars
        self.stars = []
        for i in range(20):
            star = Entity(
                model='cube',
                color=random.choice([color.yellow, color.red, color.black, color.white]),
                scale=random.uniform(0.05, 0.2),
                position=(
                    random.uniform(-15, 15),
                    random.uniform(-10, 10),
                    random.uniform(-20, -5)
                )
            )
            # Glitchy movement
            if random.random() < 0.3:
                star.animate('position', star.position + Vec3(random.uniform(-5, 5), 0, 0), duration=0.1, loop=True)
            self.stars.append(star)
    
    def update(self):
        """Update with B3313 glitches"""
        # Random glitches
        self.glitch_timer += time.dt
        if self.glitch_timer > random.uniform(2, 5):
            self.glitch_timer = 0
            self.apply_glitch()
        
        # Original interaction code
        if not mouse.locked:
            hovered_part = None
            for part_name, part in self.grabbable_parts.items():
                if distance(mouse.world_point, part.world_position) < 1:
                    hovered_part = part_name
                    break
            
            if held_keys['left mouse'] and hovered_part:
                if not self.is_being_grabbed:
                    self.is_being_grabbed = True
                    self.grabbed_part = hovered_part
                    self.grab_offset = mouse.world_point - self.grabbable_parts[hovered_part].world_position
                
                if self.is_being_grabbed:
                    target_pos = mouse.world_point - self.grab_offset
                    current_part = self.grabbable_parts[self.grabbed_part]
                    
                    stretch_amount = distance(target_pos, current_part.world_position)
                    if stretch_amount < self.max_stretch:
                        current_part.position = lerp(current_part.position, target_pos, time.dt * 10)
                        
                        stretch_factor = 1 + (stretch_amount * 0.2)
                        current_part.scale = lerp(current_part.scale, current_part.scale * stretch_factor, time.dt * 5)
            else:
                self.is_being_grabbed = False
                
                # Return parts with elastic bounce
                for part_name, part in self.grabbable_parts.items():
                    original_pos = Vec3(0, 0, 0)
                    if part_name == 'left_ear':
                        original_pos = Vec3(-1.4, 0, 0.2)
                    elif part_name == 'right_ear':
                        original_pos = Vec3(1.4, 0, 0.2)
                    elif part_name == 'nose':
                        original_pos = Vec3(0, -0.1, 1.3)
                    
                    part.position = lerp(part.position, original_pos, time.dt * self.elasticity * 10)
                    
                    original_scale = 1
                    if part_name == 'nose':
                        original_scale = Vec3(0.4, 0.3, 0.6)
                    elif 'ear' in part_name:
                        original_scale = Vec3(0.6, 0.8, 0.4)
                    elif part_name == 'head':
                        original_scale = Vec3(3, 3, 3)
                    
                    part.scale = lerp(part.scale, original_scale, time.dt * 8)
            
            # Head movement with occasional twitches
            if not self.is_being_grabbed:
                mouse_influence = Vec3(mouse.x * 0.5, mouse.y * 0.3, 0)
                if random.random() < 0.01:  # Random twitch
                    mouse_influence += Vec3(random.uniform(-10, 10), random.uniform(-10, 10), 0)
                self.rotation = lerp(self.rotation, mouse_influence, time.dt * 2)
                
                # Corrupted blink
                if random.random() < 0.01:
                    self.blink()
    
    def apply_glitch(self):
        """Apply B3313 style glitches"""
        glitch_type = random.choice(['color', 'scale', 'visibility', 'position'])
        
        if glitch_type == 'color':
            part = random.choice(list(self.grabbable_parts.values()))
            original_color = part.color
            part.color = random.choice([color.black, color.red, color.white])
            invoke(setattr, part, 'color', original_color, delay=0.2)
        
        elif glitch_type == 'scale':
            self.scale = Vec3(3 + random.uniform(-0.5, 0.5), 3, 3)
            invoke(setattr, self, 'scale', 3, delay=0.3)
        
        elif glitch_type == 'visibility':
            part = random.choice([self.left_eye, self.right_eye, self.mustache])
            if hasattr(part, 'enabled'):
                part.enabled = not part.enabled
                invoke(setattr, part, 'enabled', True, delay=0.5)
    
    def blink(self):
        """Corrupted blink"""
        original_scale_y = self.left_eye.scale_y
        blink_scale = 0.05 if random.random() > 0.2 else 0
        self.left_eye.animate('scale_y', blink_scale, duration=0.1, curve=curve.in_out_sine)
        self.right_eye.animate('scale_y', blink_scale, duration=0.1, curve=curve.in_out_sine)
        invoke(setattr, self.left_eye, 'scale_y', original_scale_y, delay=0.15)
        invoke(setattr, self.right_eye, 'scale_y', original_scale_y, delay=0.15)

# ----------- B3313 MENU SYSTEM -----------
def setup_b3313_menu():
    """Set up the B3313 corrupted menu"""
    # Clear existing entities
    for e in scene.entities:
        if e not in [camera, mouse, window.fps_counter, window.exit_button]:
            destroy(e)
    
    # Reset camera for menu
    camera.parent = scene
    camera.position = (0, 0, 10)
    camera.rotation = (0, 0, 0)
    mouse.locked = False
    
    # Dark fog effect
    scene.fog_color = color.black
    scene.fog_density = 0.05
    
    # Create corrupted Mario head
    global mario_head
    mario_head = B3313MarioHead()
    
    # Title with corruption
    title_texts = []
    title_variations = ['B3313 1.0', 'B̸3̷3̶1̴3̵', 'ERROR', 'PERSONALIZATION AI ACTIVE']
    
    for i, text in enumerate(title_variations):
        t = Text(
            text,
            position=(0, 0.35),
            origin=(0, 0),
            scale=4,
            color=color.red if i == 0 else color.black,
            enabled=(i == 0)
        )
        title_texts.append(t)
    
    # Cycle through title variations
    def cycle_title():
        current = None
        for i, t in enumerate(title_texts):
            if t.enabled:
                current = i
                t.enabled = False
                break
        next_idx = (current + 1) % len(title_texts)
        title_texts[next_idx].enabled = True
        invoke(cycle_title, delay=random.uniform(3, 8))
    
    invoke(cycle_title, delay=5)
    
    # Start text with glitches
    start_text = Text(
        'PRESS START',
        position=(0, -0.3),
        origin=(0, 0),
        scale=2,
        color=color.white
    )
    
    # Glitchy start text
    def glitch_start():
        if random.random() < 0.3:
            start_text.text = random.choice(['PRESS START', 'P̸R̷E̶S̵S̴ ̵S̶T̸A̷R̶T̵', 'ENTER', 'WAKE UP'])
        start_text.color = random.choice([color.white, color.gray, color.red])
    
    start_text.animate('color', color.gray, duration=1, curve=curve.in_out_sine, loop=True)
    Entity(update=lambda: glitch_start() if random.random() < 0.1 else None)
    
    # Cryptic messages
    messages = [
        'Every copy is personalized',
        'The AI is watching',
        'You want fun?',
        'L is real 2401',
        '⬛⬛⬛⬛⬛⬛⬛⬛'
    ]
    
    message_text = Text(
        random.choice(messages),
        position=(0, -0.45),
        origin=(0, 0),
        scale=0.8,
        color=color.dark_gray
    )
    
    # Change message occasionally
    def change_message():
        message_text.text = random.choice(messages)
        message_text.color = random.choice([color.dark_gray, color.red, color.black])
        invoke(change_message, delay=random.uniform(4, 10))
    
    invoke(change_message, delay=5)
    
    # Corrupted particles
    for i in range(15):
        particle = Entity(
            model=random.choice(['sphere', 'cube']),
            color=random.choice([color.black, color.red, color.dark_gray]),
            scale=random.uniform(0.02, 0.1),
            position=(
                random.uniform(-10, 10),
                random.uniform(-5, 5),
                random.uniform(-15, 0)
            )
        )
        # Erratic movement
        particle.animate('position', particle.position + Vec3(random.uniform(-5, 5), random.uniform(-2, 2), 0), 
                        duration=random.uniform(2, 5), curve=curve.in_out_sine, loop=True)

# ----------- B3313 PLAYER CONTROLLER -----------
class B3313PlayerController(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = 'cube'
        self.scale = Vec3(0.8, 1.8, 0.8)
        self.origin_y = -0.5
        self.collider = 'box'
        
        # Player visual with occasional corruptions
        self.hat = Entity(model='cube', scale=(1.1, 0.4, 1.1), color=color.red, position=(0, 1.05, 0), parent=self)
        self.head = Entity(model='sphere', scale=0.8, color=color.peach, position=(0, 0.6, 0), parent=self)
        self.body = Entity(model='cube', scale=(1, 1, 1), color=color.blue, position=(0, -0.1, 0), parent=self)
        
        self.camera_pivot = Entity(parent=self, y=2)
        camera.parent = self.camera_pivot
        camera.position = (0, 2, -12)
        camera.rotation = (0, 0, 0)
        camera.fov = 90
        mouse.locked = True

        self.speed = 8
        self.jump_height = 8
        self.gravity = 1.5
        self.grounded = False
        self.jump_count = 0
        self.velocity_y = 0
        self.air_time = 0
        self.corruption_timer = 0

    def update(self):
        # B3313 random corruptions
        self.corruption_timer += time.dt
        if self.corruption_timer > random.uniform(10, 30):
            self.corruption_timer = 0
            self.apply_corruption()
        
        # Movement
        self.direction = Vec3(self.forward * (held_keys['w'] - held_keys['s']) + self.right * (held_keys['d'] - held_keys['a'])).normalized()
        
        if self.direction.length() > 0:
            self.rotation = lerp(self.rotation, self.look_at(self.position + self.direction, self.up), 10 * time.dt)

        # Movement with collision
        move_amount = self.direction * self.speed * time.dt
        
        if not self.intersects(origin=self.position, direction=move_amount, distance=self.scale_x, ignore=[self, self.hat, self.head, self.body]).hit:
            self.x += move_amount.x
            self.z += move_amount.z
        
        # Gravity
        self.y += self.velocity_y * time.dt

        # Ground check
        self.grounded = False
        ground_check = boxcast(self.world_position + Vec3(0,0.1,0), direction=Vec3(0,-1,0), distance=0.2, ignore=[self, self.hat, self.head, self.body])
        if ground_check.hit:
            self.grounded = True
            self.y = ground_check.world_point.y
            self.velocity_y = 0
            self.jump_count = 0
        
        # Wall collision
        hit_info = self.intersects(ignore=[self, self.hat, self.head, self.body])
        if hit_info.hit:
            if abs(hit_info.normal.y) < 0.5:
                self.position -= hit_info.normal * hit_info.overlap
            elif self.velocity_y > 0:
                self.y -= hit_info.overlap
                self.velocity_y = 0

        # Gravity application
        if not self.grounded:
            self.velocity_y -= self.gravity * 25 * time.dt
            self.air_time += time.dt
        else:
            self.air_time = 0

        # Camera control with occasional glitches
        self.rotation_y += mouse.velocity[0] * 40
        self.camera_pivot.rotation_x -= mouse.velocity[1] * 40
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -45, 45)
        
        # Random camera shake in B3313 style
        if random.random() < 0.001:
            camera.shake(duration=0.2, magnitude=2)

        # Void death
        if self.y < -50:
            self.position = (0, 10, -10)
            self.velocity_y = 0
            state['personalization_level'] += 1
            print_on_screen("EVERY COPY IS PERSONALIZED", position=(0, 0), scale=3, duration=2, color=color.red)

    def apply_corruption(self):
        """Apply B3313 style player corruptions"""
        corruption = random.choice(['color', 'scale', 'speed'])
        
        if corruption == 'color':
            self.hat.color = random.choice([color.red, color.black, color.green])
            self.body.color = random.choice([color.blue, color.black, color.red])
            invoke(self.reset_colors, delay=random.uniform(2, 5))
        
        elif corruption == 'scale':
            self.scale = Vec3(0.8 * random.uniform(0.8, 1.2), 1.8 * random.uniform(0.9, 1.1), 0.8)
            invoke(setattr, self, 'scale', Vec3(0.8, 1.8, 0.8), delay=3)
        
        elif corruption == 'speed':
            self.speed = random.uniform(4, 12)
            invoke(setattr, self, 'speed', 8, delay=5)
    
    def reset_colors(self):
        self.hat.color = color.red
        self.body.color = color.blue

    def input(self, key):
        if key == 'space' and self.jump_count < 1:
            self.grounded = False
            self.velocity_y = self.jump_height
            self.jump_count += 1
            self.air_time = 0
            try:
                jump_sound.play()
            except:
                pass

# ----------- B3313 ENEMIES -----------
class CorruptedGoomba(Entity):
    def __init__(self, position=(0,0,0)):
        # Sometimes spawn as different enemy types
        self.enemy_type = random.choice(['goomba', 'dark_goomba', 'glitch'])
        
        colors = {
            'goomba': color.brown,
            'dark_goomba': color.black,
            'glitch': color.rgb(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        }
        
        super().__init__(
            name='goomba', 
            model='cube', 
            color=colors[self.enemy_type], 
            scale=(1, 0.7, 1),
            position=position, 
            collider='box', 
            shader=lit_with_shadows_shader
        )
        
        Entity(model='sphere', color=color.dark_gray if self.enemy_type == 'dark_goomba' else color.peach, 
               scale=(1.2, 0.5, 1.2), y=0.4, parent=self)
        
        self.direction = 1
        self.speed = random.uniform(1, 4) if self.enemy_type == 'glitch' else 2
        self.path_limit = random.uniform(3, 8)
        self.start_x = self.x

    def update(self):
        self.x += self.direction * self.speed * time.dt
        
        if self.enemy_type == 'glitch' and random.random() < 0.01:
            # Teleport randomly
            self.position += Vec3(random.uniform(-2, 2), 0, random.uniform(-2, 2))
        
        if abs(self.x - self.start_x) > self.path_limit:
            self.direction *= -1
            self.rotation_y += 180

class B3313ChainChomp(Entity):
    def __init__(self, post_position=(0,0,0)):
        self.post = Entity(model='cylinder', position=post_position, scale=(1, 5, 1), 
                          color=color.dark_gray, shader=lit_with_shadows_shader)
        
        # Sometimes spawn unchained
        self.is_chained = random.random() > 0.2
        
        super().__init__(
            name='chain_chomp', 
            model='sphere', 
            color=color.black, 
            scale=8, 
            position=post_position + Vec3(-5, 4, 0), 
            collider='sphere', 
            shader=lit_with_shadows_shader
        )
        
        # Red eyes for B3313
        Entity(model='sphere', color=color.red, scale=(0.3, 0.3, 0.3), 
               position=(-0.3, 0.2, 0.4), parent=self)
        Entity(model='sphere', color=color.red, scale=(0.3, 0.3, 0.3), 
               position=(0.3, 0.2, 0.4), parent=self)
        
        self.chain_length = 20 if self.is_chained else float('inf')
        self.state = 'idle'
        self.lunge_speed = 40
        self.retract_speed = 5
        self.detection_radius = 30

    def update(self):
        dist_to_player = distance(self, player)
        dist_to_post = distance(self, self.post)

        if self.state == 'idle' and dist_to_player < self.detection_radius:
            self.state = 'lunging'
        
        if self.state == 'lunging':
            self.look_at(player)
            self.position += self.forward * self.lunge_speed * time.dt
            
            if self.is_chained and dist_to_post > self.chain_length:
                self.state = 'retracting'
            elif not self.is_chained and dist_to_player > 50:
                # Unchained chomps teleport back
                self.position = self.post.position + Vec3(-5, 4, 0)
                self.state = 'idle'
        
        if self.state == 'retracting':
            target_pos = self.post.position + Vec3(0,4,0)
            self.look_at(target_pos)
            self.position = lerp(self.position, target_pos, time.dt * self.retract_speed)
            if distance(self, target_pos) < 1:
                self.state = 'idle'

# ----------- B3313 LEVEL GENERATION -----------
class B3313Room(Entity):
    def __init__(self, room_type='normal', position=(0,0,0)):
        super().__init__(position=position)
        self.room_type = room_type
        self.size = 40
        
        # Floor with different textures
        floor_color = color.white if room_type == 'normal' else color.dark_gray
        self.floor = Entity(
            model='plane', 
            scale=self.size, 
            texture='white_cube',
            texture_scale=(10, 10),
            color=floor_color,
            position=(0, 0, 0),
            parent=self,
            collider='box'
        )
        
        # Walls
        wall_height = 15
        wall_color = color.light_gray if room_type == 'normal' else color.black
        
        # North wall
        Entity(model='cube', scale=(self.size, wall_height, 1), 
               position=(0, wall_height/2, self.size/2), 
               color=wall_color, parent=self, collider='box')
        
        # South wall
        Entity(model='cube', scale=(self.size, wall_height, 1), 
               position=(0, wall_height/2, -self.size/2), 
               color=wall_color, parent=self, collider='box')
        
        # East wall
        Entity(model='cube', scale=(1, wall_height, self.size), 
               position=(self.size/2, wall_height/2, 0), 
               color=wall_color, parent=self, collider='box')
        
        # West wall
        Entity(model='cube', scale=(1, wall_height, self.size), 
               position=(-self.size/2, wall_height/2, 0), 
               color=wall_color, parent=self, collider='box')
        
        # Ceiling (sometimes missing)
        if random.random() > 0.3:
            Entity(model='plane', scale=self.size, rotation=(180, 0, 0),
                   position=(0, wall_height, 0), color=wall_color, parent=self)
        
        # Room-specific features
        if room_type == 'liminal':
            self.add_liminal_features()
        elif room_type == 'corrupted':
            self.add_corrupted_features()
        elif room_type == 'endless':
            self.add_endless_features()
    
    def add_liminal_features(self):
        """Add backrooms-like features"""
        # Fluorescent lights
        for i in range(3):
            light = Entity(
                model='cube',
                scale=(2, 0.2, 8),
                position=(random.uniform(-15, 15), 14, random.uniform(-15, 15)),
                color=color.yellow,
                parent=self
            )
            # Flickering effect
            if random.random() < 0.3:
                def flicker():
                    light.enabled = not light.enabled
                    invoke(flicker, delay=random.uniform(0.1, 0.5))
                flicker()
        
        # Random pillars
        for i in range(random.randint(2, 5)):
            Entity(
                model='cube',
                scale=(2, 15, 2),
                position=(random.uniform(-15, 15), 7.5, random.uniform(-15, 15)),
                color=color.gray,
                parent=self,
                collider='box'
            )
    
    def add_corrupted_features(self):
        """Add glitched/corrupted elements"""
        # Floating geometry
        for i in range(random.randint(5, 10)):
            Entity(
                model=random.choice(['cube', 'sphere']),
                scale=random.uniform(1, 3),
                position=(random.uniform(-15, 15), random.uniform(2, 12), random.uniform(-15, 15)),
                color=color.random_color(),
                rotation=(random.randint(0, 360), random.randint(0, 360), random.randint(0, 360)),
                parent=self
            ).animate('rotation', Vec3(360, 360, 360), duration=random.uniform(5, 15), loop=True)
        
        # Corrupted textures on walls
        if random.random() < 0.5:
            Entity(
                model='plane',
                scale=(10, 10),
                position=(random.choice([-19.5, 19.5]), 7, 0),
                rotation=(0, 90 if random.random() < 0.5 else -90, 0),
                color=color.red,
                parent=self
            )
    
    def add_endless_features(self):
        """Add endless hallway illusion"""
        # Mirror-like walls
        for z in range(-18, 19, 6):
            Entity(
                model='cube',
                scale=(0.5, 10, 0.5),
                position=(random.choice([-10, 10]), 5, z),
                color=color.dark_gray,
                parent=self
            )

def setup_b3313_level():
    global player, ground, current_room
    
    # Clear existing entities
    for e in scene.entities:
        if e not in [camera, mouse, window.fps_counter, window.exit_button]:
            destroy(e)

    # Reset state
    state['coins'] = 0
    state['stars'] = 0
    state['king_bobomb_throws'] = 0
    state['is_holding_king'] = False
    state['current_floor'] = 0
    state['rooms_visited'] = []
    
    # Enable fog for atmosphere
    scene.fog_color = color.rgb(20, 20, 20)
    scene.fog_density = 0.02
    
    # Player
    player = B3313PlayerController(position=(0, 5, 0), color=color.clear)
    
    # Ambient sound
    try:
        ambient_hum.play()
    except:
        pass
    
    # Generate initial room
    room_types = ['normal', 'liminal', 'corrupted', 'endless']
    current_room = B3313Room(room_type=random.choice(room_types), position=(0, 0, 0))
    state['rooms_visited'].append(current_room.position)
    
    # Add some initial entities
    # Corrupted Goombas
    for i in range(random.randint(2, 5)):
        CorruptedGoomba(position=(random.uniform(-15, 15), 0.5, random.uniform(-15, 15)))
    
    # Coins (sometimes corrupted)
    for i in range(random.randint(5, 15)):
        coin = Entity(
            name='coin', 
            model='cylinder', 
            color=color.gold if random.random() > 0.2 else color.black, 
            scale=0.5, 
            position=(random.uniform(-15, 15), 1, random.uniform(-15, 15)), 
            rotation=(90, 0, 0)
        )
        if random.random() < 0.3:
            coin.animate('y', coin.y + random.uniform(1, 3), duration=2, curve=curve.in_out_sine, loop=True)
    
    # Hidden star (B3313 style)
    star_positions = [
        (15, 12, 15),    # High corner
        (-18, 1, -18),   # Low corner
        (0, -5, 0),      # Under the floor
        (0, 20, 0),      # Above ceiling
    ]
    
    star = Entity(
        name='star', 
        model='star' if random.random() > 0.3 else 'cube', 
        color=color.yellow if random.random() > 0.2 else color.black, 
        scale=3, 
        position=random.choice(star_positions), 
        rotation_y=45, 
        enabled=random.random() > 0.5,  # Sometimes invisible
        shader=lit_with_shadows_shader
    )
    star.animate('rotation_y', 360, duration=5, loop=True)
    
    # UI with corruption
    coin_text = Text(
        text=f"Coins: {state['coins']}", 
        position=(-0.8, 0.45), 
        origin=(0, 0), 
        scale=2, 
        name='coin_text',
        color=color.white
    )
    
    star_text = Text(
        text=f"Stars: {state['stars']}", 
        position=(0.8, 0.45), 
        origin=(0, 0), 
        scale=2, 
        name='star_text',
        color=color.white
    )
    
    # Personalization indicator
    Text(
        text=f"P.LVL: {state['personalization_level']}", 
        position=(0, 0.45), 
        origin=(0, 0), 
        scale=1.5, 
        name='personalization_text',
        color=color.red
    )
    
    # Add door portals
    create_doors()

def create_doors():
    """Create mysterious doors that lead to other rooms"""
    door_positions = [
        (0, 2.5, 19.5, 'north'),
        (0, 2.5, -19.5, 'south'),
        (19.5, 2.5, 0, 'east'),
        (-19.5, 2.5, 0, 'west')
    ]
    
    for x, y, z, direction in door_positions:
        if random.random() > 0.3:  # Not all walls have doors
            door = Entity(
                name='door',
                model='cube',
                scale=(5, 5, 0.5) if direction in ['north', 'south'] else (0.5, 5, 5),
                position=(x, y, z),
                color=color.black,
                collider='box'
            )
            door.direction = direction

# ----------- MAIN GAME LOOP FOR B3313 -----------
def update():
    if state['game_mode'] == 'splash':
        return
    elif state['game_mode'] == 'menu':
        return
    
    # Game mode - B3313 gameplay
    if 'player' not in globals():
        return
    
    # Check for door transitions
    hit_info = player.intersects()
    if hit_info.hit and hasattr(hit_info.entity, 'name') and hit_info.entity.name == 'door':
        # Transition to new room
        transition_room(hit_info.entity.direction)
    
    # Enemy interactions
    hit_info = player.intersects()
    if hit_info.hit and hasattr(hit_info.entity, 'name'):
        # Stomp Logic
        if player.velocity_y < -1 and player.y > hit_info.entity.y + 0.5 and player.air_time > 0.1:
            if hit_info.entity.name == 'goomba':
                try:
                    stomp_sound.play()
                except:
                    pass
                destroy(hit_info.entity)
                player.velocity_y = 5
                
                # Sometimes spawn more enemies
                if random.random() < 0.3:
                    CorruptedGoomba(position=hit_info.entity.position + Vec3(random.uniform(-5, 5), 0, random.uniform(-5, 5)))
        
        # Damage
        elif hit_info.entity.name in ['goomba', 'chain_chomp']:
            player.position = (0, 10, 0)
            player.velocity_y = 0
            state['personalization_level'] += 1
            
            # Corruption effect
            camera.shake(duration=0.5, magnitude=5)
            print_on_screen(random.choice(['OUCH', 'ERROR', '???', '⬛⬛⬛']), 
                          position=(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)), 
                          scale=4, duration=1, color=color.red)

    # Coin Collection with corruption
    hit_info = player.intersects()
    if hit_info.hit and hasattr(hit_info.entity, 'name') and hit_info.entity.name == 'coin':
        try:
            coin_sound.play()
        except:
            pass
        
        # Sometimes coins are cursed
        if hit_info.entity.color == color.black:
            state['coins'] = max(0, state['coins'] - 1)
            print_on_screen("CURSED", position=(0, 0.2), scale=2, duration=1, color=color.red)
        else:
            state['coins'] += 1
        
        destroy(hit_info.entity)
        scene.find('coin_text').text = f"Coins: {state['coins']}"
        
        # Random coin duplication in B3313 style
        if random.random() < 0.1:
            for i in range(random.randint(2, 5)):
                Entity(
                    name='coin',
                    model='cylinder',
                    color=color.gold if random.random() > 0.3 else color.black,
                    scale=0.5,
                    position=hit_info.entity.position + Vec3(random.uniform(-2, 2), 0, random.uniform(-2, 2)),
                    rotation=(90, 0, 0)
                )

    # Star Collection
    star = scene.find('star')
    if star and star.enabled and distance(player, star) < 4:
        try:
            star_sound.play()
        except:
            pass
        destroy(star)
        state['stars'] += 1
        scene.find('star_text').text = f"Stars: {state['stars']}"
        
        # B3313 star message
        messages = [
            "YOU GOT A STAR!",
            "ANOTHER SOUL COLLECTED",
            "THE PERSONALIZATION CONTINUES",
            f"STAR #{state['stars']}... BUT AT WHAT COST?",
            "⭐⭐⭐⭐⭐"
        ]
        print_on_screen(random.choice(messages), position=(0, 0), scale=5, duration=3, color=color.yellow)
        
        # Sometimes warp player
        if random.random() < 0.3:
            player.position = Vec3(random.uniform(-15, 15), 5, random.uniform(-15, 15))
            print_on_screen("WHERE AM I?", position=(0, -0.2), scale=3, duration=2, color=color.red)
    
    # Update personalization text
    if scene.find('personalization_text'):
        scene.find('personalization_text').text = f"P.LVL: {state['personalization_level']}"
        
        # Increase corruption with personalization
        if state['personalization_level'] > 5:
            scene.fog_density = 0.02 + (state['personalization_level'] * 0.005)
        
        if state['personalization_level'] > 10:
            # Start reality breaking
            if random.random() < 0.001 * state['personalization_level']:
                camera.fov = random.randint(60, 120)
                invoke(setattr, camera, 'fov', 90, delay=0.5)

def transition_room(direction):
    """Transition to a new B3313 room"""
    global current_room
    
    # Fade effect
    fade = Entity(model='cube', scale=100, color=color.black, alpha=0)
    fade.animate('alpha', 1, duration=0.3)
    
    def create_new_room():
        # Destroy old room
        destroy(current_room)
        
        # Create new room with increasing corruption
        room_types = ['normal', 'liminal', 'corrupted', 'endless']
        weights = [1, 2, 3 + state['personalization_level'], 1 + state['personalization_level']]
        
        room_type = random.choices(room_types, weights=weights)[0]
        current_room = B3313Room(room_type=room_type, position=(0, 0, 0))
        
        # Move player to opposite side
        positions = {
            'north': (0, 5, -18),
            'south': (0, 5, 18),
            'east': (-18, 5, 0),
            'west': (18, 5, 0)
        }
        player.position = positions[direction]
        
        # Spawn new entities
        spawn_room_entities(room_type)
        
        # Create new doors
        create_doors()
        
        # Fade back
        fade.animate('alpha', 0, duration=0.3)
        destroy(fade, delay=0.4)
        
        state['current_floor'] += 1
        
        # Creepy messages
        if state['current_floor'] % 5 == 0:
            messages = [
                f"FLOOR -{state['current_floor']}",
                "DEEPER AND DEEPER",
                "NO ESCAPE",
                "THE CASTLE REMEMBERS",
                "YOU'VE BEEN HERE BEFORE"
            ]
            print_on_screen(random.choice(messages), position=(0, 0.3), scale=3, duration=3, color=color.red)
    
    invoke(create_new_room, delay=0.3)

def spawn_room_entities(room_type):
    """Spawn entities based on room type"""
    if room_type == 'corrupted':
        # More enemies
        for i in range(random.randint(3, 8)):
            CorruptedGoomba(position=(random.uniform(-15, 15), 0.5, random.uniform(-15, 15)))
        
        # Unchained chomp chance
        if random.random() < 0.3:
            B3313ChainChomp(post_position=(0, 0, 0))
    
    elif room_type == 'liminal':
        # Fewer enemies, more coins
        for i in range(random.randint(10, 20)):
            Entity(
                name='coin',
                model='cylinder',
                color=color.gold,
                scale=0.5,
                position=(random.uniform(-18, 18), 1, random.uniform(-18, 18)),
                rotation=(90, 0, 0)
            )
    
    elif room_type == 'endless':
        # Repeating pattern of entities
        for z in range(-15, 16, 5):
            Entity(
                name='coin',
                model='cylinder',
                color=color.gold if z % 2 == 0 else color.black,
                scale=0.5,
                position=(0, 1, z),
                rotation=(90, 0, 0)
            )
    
    # Random star placement
    if random.random() < 0.2:
        star = Entity(
            name='star',
            model='star',
            color=color.yellow if random.random() > 0.1 else color.black,
            scale=3,
            position=(random.uniform(-15, 15), random.uniform(1, 10), random.uniform(-15, 15)),
            rotation_y=45,
            shader=lit_with_shadows_shader
        )
        star.animate('rotation_y', 360, duration=5, loop=True)

def input(key):
    global mario_head
    
    if state['game_mode'] == 'splash':
        # Skip splash
        if key in ['space', 'enter', 'escape']:
            state['game_mode'] = 'menu'
            setup_b3313_menu()
    
    elif state['game_mode'] == 'menu':
        if key in ['space', 'enter']:
            state['game_mode'] = 'game'
            setup_b3313_level()
        elif key == 'escape':
            application.quit()
    
    else:
        # Game input
        if key == 'r':
            setup_b3313_level()
        elif key == 'escape':
            state['game_mode'] = 'menu'
            setup_b3313_menu()
        
        # Debug keys
        if key == 'p':
            state['personalization_level'] += 5
            print(f"Personalization Level: {state['personalization_level']}")
        
        if key == 'f':
            window.fullscreen = not window.fullscreen

# ----------- INITIALIZE B3313 -----------
# Dark sky for B3313
sky = Sky(color=color.rgb(10, 10, 10))

# Dim lighting for atmosphere
DirectionalLight(y=50, z=50, x=50, shadows=True, shadow_map_resolution=(2048,2048), color=color.rgb(200, 200, 200))
AmbientLight(color=color.rgb(50, 50, 50))

# Start with splash screen
show_splash_screen()

# Run the cursed game
app.run()
