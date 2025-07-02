# test.py
from ursina import *
from ursina.shaders import lit_with_shadows_shader
import math

# ----------- GAME SETUP -----------
app = Ursina()
window.title = 'Super Ursina 64'
window.fps_counter.enabled = True
window.exit_button.visible = False

# ----------- GAME STATE & ASSETS -----------
state = {
    'coins': 0,
    'stars': 0,
    'king_bobomb_throws': 0,
    'is_holding_king': False,
}
# Sounds
coin_sound = Audio('coin', loop=False, autoplay=False)
stomp_sound = Audio('hit', loop=False, autoplay=False)
star_sound = Audio('powerup', loop=False, autoplay=False)
jump_sound = Audio('jump', loop=False, autoplay=False)
chomp_lunge_sound = Audio('laser_shoot', loop=False, autoplay=False) # Placeholder

# ----------- PLAYER CONTROLLER (ENGINE OVERHAUL) -----------
class ThirdPersonController(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = 'cube'
        self.scale = Vec3(0.8, 1.8, 0.8)
        self.origin_y = -0.5
        self.collider = 'box'
        
        # Player visual components
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

    def update(self):
        # --- 1. INPUT & ROTATION ---
        self.direction = Vec3(self.forward * (held_keys['w'] - held_keys['s']) + self.right * (held_keys['d'] - held_keys['a'])).normalized()
        
        if self.direction.length() > 0:
            self.rotation = lerp(self.rotation, self.look_at(self.position + self.direction, self.up), 10 * time.dt)

        # --- 2. MOVEMENT & COLLISION (AXIS-SEPARATED) ---
        # Move on X/Z plane
        move_amount = self.direction * self.speed * time.dt
        
        # A simple raycast check before moving to prevent clipping through thin walls
        if not self.intersects(origin=self.position, direction=move_amount, distance=self.scale_x, ignore=[self, self.hat, self.head, self.body]).hit:
            self.x += move_amount.x
            self.z += move_amount.z
        
        # Y-axis movement (Gravity)
        self.y += self.velocity_y * time.dt

        # --- 3. GROUND & COLLISION CHECK ---
        self.grounded = False
        # Use a boxcast down to check for ground
        ground_check = boxcast(self.world_position + Vec3(0,0.1,0), direction=Vec3(0,-1,0), distance=0.2, ignore=[self, self.hat, self.head, self.body])
        if ground_check.hit:
            self.grounded = True
            self.y = ground_check.world_point.y
            self.velocity_y = 0
            self.jump_count = 0
        
        # General intersection for walls and ceilings
        hit_info = self.intersects(ignore=[self, self.hat, self.head, self.body])
        if hit_info.hit:
            if abs(hit_info.normal.y) < 0.5: # It's a wall
                self.position -= hit_info.normal * hit_info.overlap
            elif self.velocity_y > 0: # Hit a ceiling
                self.y -= hit_info.overlap
                self.velocity_y = 0

        # Apply gravity if not grounded
        if not self.grounded:
            self.velocity_y -= self.gravity * 25 * time.dt
            self.air_time += time.dt
        else:
            self.air_time = 0

        # --- 4. CAMERA & FALL CHECK ---
        self.rotation_y += mouse.velocity[0] * 40
        self.camera_pivot.rotation_x -= mouse.velocity[1] * 40
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -45, 45)

        if self.y < -20:
            self.position = (0, 10, -10)
            self.velocity_y = 0

    def input(self, key):
        if key == 'space' and self.jump_count < 1:
            self.grounded = False
            self.velocity_y = self.jump_height
            self.jump_count += 1
            self.air_time = 0
            jump_sound.play()

# ----------- ENEMY CLASSES -----------
class Goomba(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            name='goomba', model='cube', color=color.brown, scale=(1, 0.7, 1),
            position=position, collider='box', shader=lit_with_shadows_shader
        )
        Entity(model='sphere', color=color.peach, scale=(1.2, 0.5, 1.2), y=0.4, parent=self)
        self.direction = 1
        self.speed = 2
        self.path_limit = 5
        self.start_x = self.x

    def update(self):
        self.x += self.direction * self.speed * time.dt
        if abs(self.x - self.start_x) > self.path_limit:
            self.direction *= -1
            self.rotation_y += 180

class KingBobomb(Entity):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            name='king_bobomb', model='sphere', color=color.black, scale=4,
            position=position, collider='sphere', shader=lit_with_shadows_shader
        )
        self.crown = Entity(model='cube', color=color.gold, scale=(0.5, 0.2, 0.5), y=0.6, parent=self)
        self.state = 'wandering' # states: wandering, held, thrown, stunned
        self.velocity = Vec3(0,0,0)

    def update(self):
        if self.state == 'wandering':
            if random.random() < 0.01:
                target_pos = self.position + Vec3(random.uniform(-5,5), 0, random.uniform(-5,5))
                self.animate_position(target_pos, duration=2, curve=curve.ease_in_out)
        
        elif self.state == 'thrown':
            # Physics-based throw
            self.position += self.velocity * time.dt
            self.velocity.y -= 30 * time.dt # King's own gravity
            self.rotation_y += 360 * time.dt

            hit_info = self.intersects(ignore=[player])
            if hit_info.hit:
                self.velocity = Vec3(0,0,0)
                self.state = 'stunned'
                self.rotation = (0,0,0)
                
                state['king_bobomb_throws'] += 1
                print(f"King Bob-omb hits: {state['king_bobomb_throws']}/3")
                if state['king_bobomb_throws'] >= 3:
                    destroy(self)
                    scene.find('star').enabled = True
                    print("King Bob-omb defeated! A star appears!")
                else:
                    self.shake(duration=1)
                    invoke(setattr, self, 'state', 'wandering', delay=3)

class ChainChomp(Entity):
    def __init__(self, post_position=(0,0,0)):
        self.post = Entity(model='cylinder', position=post_position, scale=(1, 5, 1), color=color.dark_gray, shader=lit_with_shadows_shader)
        super().__init__(
            name='chain_chomp', model='sphere', color=color.black, scale=8, 
            position=post_position + Vec3(-5, 4, 0), 
            collider='sphere', shader=lit_with_shadows_shader
        )
        self.chain_length = 20
        self.state = 'idle' # idle, lunging, retracting
        self.lunge_speed = 35
        self.retract_speed = 5
        self.detection_radius = 25

    def update(self):
        dist_to_player = distance(self, player)
        dist_to_post = distance(self, self.post)

        if self.state == 'idle' and dist_to_player < self.detection_radius:
            self.state = 'lunging'
            chomp_lunge_sound.play()
        
        if self.state == 'lunging':
            self.look_at(player)
            self.position += self.forward * self.lunge_speed * time.dt
            if dist_to_post > self.chain_length:
                self.state = 'retracting'
        
        if self.state == 'retracting':
            target_pos = self.post.position + Vec3(0,4,0)
            self.look_at(target_pos)
            self.position = lerp(self.position, target_pos, time.dt * self.retract_speed)
            if distance(self, target_pos) < 1:
                self.state = 'idle'

# ----------- LEVEL SETUP -----------
def setup_level():
    global player, king_bobomb, ground
    
    # Clean up previous entities
    for e in scene.entities:
        if e not in [camera, mouse, window.fps_counter, window.exit_button]:
            destroy(e)

    # Reset state
    state['coins'] = 0
    state['stars'] = 0
    state['king_bobomb_throws'] = 0
    state['is_holding_king'] = False
    
    # Player
    player = ThirdPersonController(position=(0, 5, -20), color=color.clear)

    # Environment
    ground = Entity(model='plane', scale=200, texture='grass', texture_scale=(50,50), collider='box')
    
    # --- PEACH'S CASTLE ---
    castle_parent = Entity(position=(0, 0, 40), shader=lit_with_shadows_shader)
    # Main Keep
    Entity(model='cylinder', scale=(20, 30, 20), color=color.light_gray, parent=castle_parent)
    Entity(model='cone', scale=(22, 15, 22), y=22.5, color=color.red, parent=castle_parent)
    # Entrance
    Entity(model='cube', scale=(10, 12, 8), y=-9, z=-12, color=color.white, parent=castle_parent)
    Entity(model='cube', scale=(6, 8, 1), y=-11, z=-16.5, color=color.black, parent=castle_parent) # Doorway
    # Side Towers
    for i in [-1, 1]:
        Entity(model='cylinder', scale=(10, 20, 10), x=15*i, y=-5, color=color.light_gray, parent=castle_parent)
        Entity(model='cone', scale=(11, 10, 11), x=15*i, y=5, color=color.red, parent=castle_parent)

    # King Bob-omb's Arena on a hill
    Entity(model='cylinder', position=(80, -10, 60), scale=(60, 20, 60), color=color.gray)
    king_bobomb = KingBobomb(position=(80, 5, 60))

    # Chain Chomp
    ChainChomp(post_position=(-40, 0, 0))

    # Coins
    for i in range(10):
        Entity(name='coin', model='cylinder', color=color.gold, scale=0.5, position=(random.uniform(-10,10), 1, random.uniform(-10,10)), rotation=(90,0,0))

    # Goombas
    Goomba(position=(5, 0.5, 5))
    Goomba(position=(-5, 0.5, 10))
    
    # Star (initially hidden)
    star = Entity(name='star', model='star', color=color.yellow, scale=3, position=(80, 8, 60), rotation_y=45, enabled=False, shader=lit_with_shadows_shader)
    star.animate('rotation_y', 360, duration=5, loop=True)

    # UI
    Text(text="Coins: 0", position=(-0.8, 0.45), origin=(0,0), scale=2, name='coin_text')
    Text(text="Stars: 0", position=(0.8, 0.45), origin=(0,0), scale=2, name='star_text')

# ----------- MAIN GAME LOOP -----------
def update():
    # --- Player-Enemy Interaction ---
    hit_info = player.intersects()
    if hit_info.hit and hasattr(hit_info.entity, 'name'):
        # Stomp Logic: Check if player is falling and is above the enemy
        if player.velocity_y < -1 and player.y > hit_info.entity.y + 0.5 and player.air_time > 0.1:
            if hit_info.entity.name == 'goomba':
                stomp_sound.play()
                destroy(hit_info.entity)
                player.velocity_y = 5 # Bounce
        # Damage Logic
        elif hit_info.entity.name in ['goomba', 'chain_chomp']:
            player.position = (0, 10, -10) # Reset player
            player.velocity_y = 0

    # --- Coin Collection ---
    hit_info = player.intersects()
    if hit_info.hit and hasattr(hit_info.entity, 'name') and hit_info.entity.name == 'coin':
        coin_sound.play()
        destroy(hit_info.entity)
        state['coins'] += 1
        scene.find('coin_text').text = f"Coins: {state['coins']}"

    # --- King Bob-omb Interaction ---
    if state['is_holding_king']:
        king_bobomb.position = player.position + player.up * 1.5 + player.forward * 1
        king_bobomb.rotation = player.rotation
        if not held_keys['left mouse']:
            throw_king()

    # --- Star Collection ---
    star = scene.find('star')
    if star and star.enabled and distance(player, star) < 4:
        star_sound.play()
        destroy(star)
        state['stars'] += 1
        scene.find('star_text').text = f"Stars: {state['stars']}"
        print_on_screen("YOU GOT A STAR!", position=(0,0), scale=5, duration=3)

def input(key):
    if key == 'r':
        setup_level()
    if key == 'left mouse down' and not state['is_holding_king']:
        # Check if player is behind King Bob-omb to pick him up
        if king_bobomb and king_bobomb.state == 'wandering' and distance(player, king_bobomb) < 5:
            # --- FIX IS HERE ---
            # Use the .dot() method on the vector, not a standalone function.
            dot_product = player.forward.dot((king_bobomb.position - player.position).normalized())
            if dot_product > 0.5: # Player is generally facing the king
                state['is_holding_king'] = True
                king_bobomb.state = 'held'
    if key == 'left mouse up' and state['is_holding_king']:
        throw_king()

def throw_king():
    if not state['is_holding_king']: return
    
    state['is_holding_king'] = False
    king_bobomb.state = 'thrown'
    
    # Physics-based throw
    throw_force = 25
    upward_force = 8
    king_bobomb.velocity = (player.forward * throw_force) + (player.up * upward_force)

# ----------- INITIALIZE -----------
Sky()
DirectionalLight(y=50, z=50, x=50, shadows=True, shadow_map_resolution=(2048,2048))
setup_level()
app.run()
