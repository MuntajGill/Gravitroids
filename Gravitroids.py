import pygame
import random
import math
import sys

WIDTH, HEIGHT = 1536, 864
GRAVITY_CONSTANT = 10
PLANET_RADIUS_SCALE = 1.5
MAX_PLANETS = 8
TICK_RATE = 60
TIME_SCALE = 0.5  

BULLET_SPEED = 8  
MAX_PLAYER_SPEED = 4
MAX_BULLETS = 50
POINTS_PREV = None

GRADIENT_CACHED = None

# Colors
BLACK = (0, 0, 0)
TRANSLUCENT_WHITE = (255, 255, 255, 128) 
TEXT_COLOR = (255, 255, 255)

# Initialize Pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravitroids")
clock = pygame.time.Clock()

shoot_sound = pygame.mixer.Sound("sounds/shoot.ogg")
shoot_sound.set_volume(0.5)
shoot_sound = pygame.mixer.Sound("sounds/shoot.ogg")
shoot_sound.set_volume(0.5)

explosion_sound = pygame.mixer.Sound("sounds/break.ogg")
explosion_sound.set_volume(0.2)

thrusting_sound = pygame.mixer.Sound("sounds/thrusting.ogg")
thrusting_sound.set_volume(0.1)
thrusting = False

music_levels = {
    "low": "music/music_low.mp3",
    "mid": "music/music_mid.mp3",
    "high": "music/music_high.mp3"
}
current_music_level = None

def update_music(points, fade_time=1000):  # fade_time in milliseconds
    global current_music_level

    # Determine music level based on points
    if points < 50:
        new_level = "low"
    elif points < 100:
        new_level = "mid"
    else:
        new_level = "high"

    # Only change music if the level has changed
    if new_level != current_music_level:
        pygame.mixer.music.fadeout(fade_time)  # Smoothly fade out current music
        pygame.mixer.music.load(music_levels[new_level])
        pygame.mixer.music.play(-1, fade_ms=fade_time)  # Smoothly fade in new music
        current_music_level = new_level



def predict_trajectory(player, planets, steps=60, dt=0.5):
    pos = pygame.Vector2(player.x, player.y)
    vel = pygame.Vector2(player.vx, player.vy)
    trajectory_points = [pos.xy]

    for _ in range(steps):
        total_acc = pygame.Vector2(0, 0)
        for planet in planets:
            direction = pygame.Vector2(planet.x, planet.y) - pos
            distance = direction.length()
            if distance < planet.radius:
                # Stop prediction on collision
                return trajectory_points, True
            if distance > 0:
                force_mag = GRAVITY_CONSTANT * planet.mass / (distance ** 2)
                acc = direction.normalize() * force_mag
                total_acc += acc

        # Update velocity and position
        vel += total_acc * dt
        pos += vel * dt
        trajectory_points.append(pos.xy)

    return trajectory_points, False


def create_glow_texture(radius, color, mass):
    glow_radius = int(radius * 0.5)  # Glow radius scaled down
    glow_radius_squared = glow_radius * glow_radius  # Precompute squared radius
    glow_texture = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

    if mass <= 50:
        resolution_factor = 1.0  # Full resolution for planets with mass ≤ 50
    else:
        resolution_factor = 1.0 / (1 + (mass - 50) / 100)  # Slower decay
    step = max(1, int(1 / resolution_factor))  # The higher the factor, the fewer the pixels to render

    for x in range(-glow_radius, glow_radius, step):
        for y in range(-glow_radius, glow_radius, step):
            dist_squared = x**2 + y**2  # Use squared distance to avoid sqrt
            if dist_squared < glow_radius_squared:
                intensity = max(0, 255 - (dist_squared / glow_radius_squared) * 255)
                glow_color = (
                    min(int(color[0] + intensity), 255),
                    min(int(color[1] + intensity), 255),
                    min(int(color[2] + intensity), 255),
                    int(intensity)
                )
                glow_texture.set_at((x + glow_radius, y + glow_radius), glow_color)

    return glow_texture

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.radius = 5

    def update(self):
        rad_angle = math.radians(self.angle)
        self.x += self.speed * math.cos(rad_angle)
        self.y -= self.speed * math.sin(rad_angle)  # Negative because Pygame's y-axis is inverted

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius)

class Player:
    def __init__(self, x, y, angle, radius):
        self.x = x
        self.y = y
        self.angle = angle  # In degrees
        self.vx = 0  # Velocity in the x direction
        self.vy = 0  # Velocity in the y direction
        self.max_speed = MAX_PLAYER_SPEED
        self.acceleration = 0.1  # Acceleration
        self.bullets = []
        self.is_moving = False  # To track if the player is holding the move button
        self.radius = radius
        self.points = 10
        self.mass = (10/5)**0.5

    def move_forward(self):
        # Apply acceleration to the velocity
        rad_angle = math.radians(self.angle)
        self.vx += self.acceleration * math.cos(rad_angle)
        self.vy -= self.acceleration * math.sin(rad_angle)  # Negative because Pygame's y-axis is inverted

        # Limit the velocity to the max speed
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.vx *= scale
            self.vy *= scale

    def turn_left(self):
        self.angle = (self.angle + 3) % 360

    def turn_right(self):
        self.angle = (self.angle - 3) % 360

    def shoot(self):
        if len(self.bullets) < MAX_BULLETS:
            bullet = Bullet(self.x, self.y, self.angle)
            self.bullets.append(bullet)
            shoot_sound.play()

    def update(self, planets):
        gravity_x, gravity_y = self.player_gravity(planets)      
        magnitude = (gravity_x**2 + gravity_y**2)**0.5
        if magnitude != 0:
            norm_x = gravity_x / magnitude
            norm_y = gravity_y / magnitude
        else:
            norm_x, norm_y = 0, 0  # This could be any direction you prefer
        #pygame.draw.line(screen, (0, 255, 0, 128), (self.x, self.y), (self.x + norm_x * 25, self.y + norm_y * 25), 6)  # Green, longer, translucent arrow
        
        # Update position based on velocity and gravity
        self.vx += gravity_x  # Apply gravity to velocity
        self.vy += gravity_y  # Apply gravity to velocity
        
        # Update position based on velocity
        self.x += self.vx
        self.y += self.vy

        # Update bullets
        for bullet in self.bullets:
            bullet.update()

        # Remove bullets that go out of bounds
        self.bullets = [bullet for bullet in self.bullets if 0 < bullet.x < WIDTH and 0 < bullet.y < HEIGHT]

    def draw(self, screen):
        # Draw player as a triangle
        rad_angle = math.radians(self.angle)
        front_x = self.x + 20 * math.cos(rad_angle)
        front_y = self.y - 20 * math.sin(rad_angle)
        left_x = self.x + 10 * math.cos(rad_angle + math.pi / 2)
        left_y = self.y - 10 * math.sin(rad_angle + math.pi / 2)
        right_x = self.x + 10 * math.cos(rad_angle - math.pi / 2)
        right_y = self.y - 10 * math.sin(rad_angle - math.pi / 2)

        pygame.draw.polygon(screen, (255, 255, 255), [(front_x, front_y), (left_x, left_y), (right_x, right_y)])

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)
            
    def offscreen(self):
        #        if self.x < -self.radius or self.x > WIDTH + self.radius or self.y < -self.radius or self.y > HEIGHT + self.radius:
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.x = WIDTH // 2
            self.y = HEIGHT // 2
            self.vx = 0
            self.vy = 0
            self.points -= 40
        # Using list comprehension to filter bullets within screen bounds
        self.bullets = [bullet for bullet in self.bullets if not (bullet.x < -bullet.radius or bullet.x > WIDTH + bullet.radius or bullet.y < -bullet.radius or bullet.y > HEIGHT + bullet.radius)]
        
    def player_gravity(self, planets):
        mass = self.mass
        gravity_x, gravity_y = 0, 0
        for planet in planets:
            dx = planet.x - self.x
            dy = planet.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance == 0:
                continue  # Skip if no distance to avoid division by zero
            force = GRAVITY_CONSTANT/2 * mass * planet.mass / distance**2  # Simplified gravitational force
            angle = math.atan2(dy, dx)
            gravity_x += force * math.cos(angle)
            gravity_y += force * math.sin(angle)
        
        return gravity_x.real, gravity_y.real


# Planet class
class Planet:
    def __init__(self, x, y, mass, velocity, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.velocity = velocity
        self.radius = int((mass ** (3/4)) * PLANET_RADIUS_SCALE)
        self.color = color
        self.glow_texture = create_glow_texture(int(self.radius*3), self.color, self.mass)
        self.name = self.generate_name()

    def generate_name(self):
        # Scientific-sounding name generation using prefixes and suffixes
        prefixes = ["Alpha", "Beta", "Gamma", "Zeta", "Delta", "Epsilon"]
        suffixes = ["Centauri", "Taurus", "Nebula", "Andromeda", "Aurora", "Pulsar"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        return f"{prefix} {suffix}"

    def draw(self):
        # Draw the glow effect using the planet's color
        glow_rect = self.glow_texture.get_rect(center=(self.x, self.y))
        screen.blit(self.glow_texture, glow_rect)
        
        # Draw the planet itself
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def update_position(self, time_scale):
        self.x += self.velocity[0] * time_scale
        self.y += self.velocity[1] * time_scale

    def is_offscreen(self):
        return self.x < -self.radius or self.x > WIDTH + self.radius or self.y < -self.radius or self.y > HEIGHT + self.radius

    def is_clicked(self, mouse_x, mouse_y):
        # Check if the mouse click is inside the planet's circle
        return (mouse_x - self.x) ** 2 + (mouse_y - self.y) ** 2 <= self.radius ** 2
    
    def split(self, bullet):
            # Split the planet into two smaller planets with adjusted mass and velocity        
            rad_angle = math.radians(bullet.angle)
            
            perp_velocity_x =bullet.speed * math.sin(rad_angle) 
            perp_velocity_y =bullet.speed * math.cos(rad_angle)

            x = math.sin(rad_angle) * self.radius * (1/2**(0.5))
            y = math.cos(rad_angle)* self.radius * (1/2**(0.5))
            
            new_planet_1 = Planet(
                x=self.x + x,
                y=self.y + y, 
                velocity = [perp_velocity_x, perp_velocity_y], 
                mass=self.mass / 2,  # Dividing mass into two
                color = self.color
            )

            new_planet_2 = Planet(
                x=self.x - x, 
                y=self.y - y,
                velocity = [-perp_velocity_x, -perp_velocity_y], #im gonna kms
                mass=self.mass / 2,
                color = self.color
            )
            return new_planet_1, new_planet_2

# Helper functions
def spawn_planet(x=None, y=None):
    if x is None or y is None:
        # Spawn planet randomly off-screen
        side = random.choice(["left", "right", "top", "bottom"])
        if side == "left":
            x, y = -20, random.randint(0, HEIGHT)
        elif side == "right":
            x, y = WIDTH + 20, random.randint(0, HEIGHT)
        elif side == "top":
            x, y = random.randint(0, WIDTH), -20
        else:
            x, y = random.randint(0, WIDTH), HEIGHT + 20

    mass = random.uniform(5, 50)

    # Constrain velocity to ensure the planet moves into the visible area
    direction_x = WIDTH / 2 - x
    direction_y = HEIGHT / 2 - y
    distance = math.sqrt(direction_x**2 + direction_y**2)

    # Normalize direction vector
    direction_x /= distance
    direction_y /= distance

    # Add random variation to the initial velocity
    angle_bias = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle bias
    speed = random.uniform(0.5, 2.0)  # Adjust speed range as needed
    velocity = [
        speed * (direction_x * math.cos(angle_bias) - direction_y * math.sin(angle_bias)),
        speed * (direction_x * math.sin(angle_bias) + direction_y * math.cos(angle_bias)),
    ]
    
    color = (
        random.randint(50, 255),  # Random red component
        random.randint(50, 255),  # Random green component
        random.randint(50, 255),  # Random blue component
    )
    return Planet(x, y, mass, velocity, color)

def calculate_gravitational_force(planet1, planet2):
    dx = planet2.x - planet1.x
    dy = planet2.y - planet1.y
    distance = math.sqrt(dx**2 + dy**2)
    if distance <= planet1.radius + planet2.radius:
        return None  # Collision
    force = GRAVITY_CONSTANT * planet1.mass * planet2.mass / distance**1.75
    angle = math.atan2(dy, dx)
    return force * math.cos(angle), force * math.sin(angle)

def is_space_empty(x, y, planets, min_distance=50):
    # Check if the space is empty (i.e., the distance from any planet is greater than a threshold)
    for planet in planets:
        dist = math.sqrt((x - planet.x) ** 2 + (y - planet.y) ** 2)
        if dist < planet.radius + min_distance:
            return False
    return True


def check_collision(entity, target):
    distance = math.sqrt((entity.x - target.x)**2 + (entity.y - target.y)**2)
    return distance < entity.radius + target.radius

def show_death_screen():
    screen.fill(BLACK)

    # Display "You Died"
    if thrusting:
        thrusting_sound.stop()
    font = pygame.font.Font(None, 74)
    died_text = font.render("You Died", True, (255, 0, 0))
    if player.points > 0:
        reason_text = font.render("Reason: planet collision", True, (128, 128, 128))
    else:
        reason_text = font.render("Reason: ran out of points", True, (128, 128, 128))
    died_text_rect = died_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    reason_text_rect = reason_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(died_text, died_text_rect)
    screen.blit(reason_text, reason_text_rect)

    # Display points with a smaller font
    points_font = pygame.font.Font(None, 50)  # Smaller font size
    points_text = points_font.render(f"Points: {player.points}", True, (255, 255, 255))
    points_text_rect = points_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(points_text, points_text_rect)

    # Display restart instructions
    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render("Press R to Restart or Q to Quit", True, (255, 255, 255))
    restart_text_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
    screen.blit(restart_text, restart_text_rect)


    pygame.display.flip()

    # Wait for the user to choose restart or quit
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return  # Exit the function
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Restart
                    return "restart"
                elif event.key == pygame.K_q:  # Quit
                    pygame.quit()
                    return  # Exit the function
                
def reset_game():
    global player, planets
    # Reinitialize the player and planets
    player = Player(WIDTH // 2, HEIGHT // 2, 0, 15)
    planets = []  # Clear the existing planets
    
def show_title_screen():
    clock = pygame.time.Clock()
    angle_alpha = 0
    angle_beta = 0
    frame = 0

    def draw_orbiting_circles(radius):
        center_x, center_y = WIDTH // 2, HEIGHT // 2 - 270
        radius = 50
        pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y), radius)  # Base circle
        num_orbitals = 6
        for i in range(num_orbitals):
            orbital_angle = math.radians(angle_alpha + (360 / num_orbitals) * i)
            x = center_x + int(radius * 1.5 * math.cos(orbital_angle))
            y = center_y + int(radius * 1.5 * math.sin(orbital_angle))
            pygame.draw.circle(screen, (255, 0, 255), (x, y), 10)  # Smaller orbiting circles
        num_orbitals = 10
        for i in range(num_orbitals):
            orbital_angle = math.radians(angle_beta + (360 / num_orbitals) * i)
            x = center_x + int(radius * 2 * math.cos(orbital_angle))
            y = center_y + int(radius * 2 * math.sin(orbital_angle))
            pygame.draw.circle(screen, (0, 255, 255), (x, y), 10)  # Smaller orbiting circles        
        

    while True:
        draw_gradient_background()

        # Orbiting circles
        draw_orbiting_circles(50)

        # Game title and objective
        font = pygame.font.SysFont("arial", 68)
        title_text = font.render("Planet Breaker", True, (255, 255, 255))
        title_text_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110))
        screen.blit(title_text, title_text_rect)

        objective_font = pygame.font.Font(None, 50)
        objective_text = objective_font.render("Break planets. Avoid collisions.", True, (255, 255, 255))
        objective_text_rect = objective_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(objective_text, objective_text_rect)

        # Controls
        controls_font = pygame.font.Font(None, 36)
        controls_text = [
            "Thrust: Up | Turn: Left/Right",
            "Pause: K | Shoot: Space",
        ]
        for i, line in enumerate(controls_text):
            line_text = controls_font.render(line, True, (200, 200, 200))
            line_text_rect = line_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20 + (i * 30)))
            screen.blit(line_text, line_text_rect)

        # Start instructions
        def pulsating_text(text, font, color, center, frame):
            """Draw pulsating text on the screen."""
            alpha = abs((frame % 100) - 50) * 5  # Pulsating effect
            text_surface = font.render(text, True, color)
            text_surface.set_alpha(alpha)
            text_rect = text_surface.get_rect(center=center)
            screen.blit(text_surface, text_rect)
        
        
        pulsating_text("Press Enter to start or Q to quit", pygame.font.Font(None, 36), (255, 255, 255), (WIDTH // 2, HEIGHT // 2 + 200), frame)
        frame += 1

        pygame.display.flip()
        clock.tick(60)

        # Rotate circles
        angle_alpha = (angle_alpha + 1) % 360
        angle_beta = (angle_beta + 1.5) % 360

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "start"
                elif event.key == pygame.K_q:
                    pygame.quit()
                    return "quit"
                
def draw_gradient_background():
    for y in range(HEIGHT):
        color = (
            int(10 + y * 0.05),  # Red: starts at 10, increases slightly
            int(10 + y * 0.05),  # Green: same as red for a smooth blend
            int(30 + y * 0.1)    # Blue: starts darker, increases faster
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
        
def draw_dynamic_gradient():
    global GRADIENT_CACHED

    player_points = player.points

    GRADIENT_CACHED = pygame.Surface((WIDTH, HEIGHT))
    thresholds = [0, 50, 100, 150]  # Black at 0, Blue at 50, Green at 100, Red at 150+
    colors = [
        (0, 0, 0),      # Black (0 points)
        (30, 30, 150),  # Blue (50 points)
        (30, 150, 30),  # Green (100 points)
        (150, 30, 30)   # Red (150+ points)
    ]
    if player_points <= thresholds[0]:
        color_start, color_end = colors[0], colors[0]
        t = 0  # No interpolation needed
    elif player_points >= thresholds[-1]:
        color_start, color_end = colors[-1], colors[-1]
        t = 0  # No interpolation needed
    else:
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= player_points < thresholds[i + 1]:
                color_start = colors[i]
                color_end = colors[i + 1]
                t = (player_points - thresholds[i]) / (thresholds[i + 1] - thresholds[i])
                break

    for y in range(HEIGHT):
        red = int(color_start[0] + (color_end[0] - color_start[0]) * t)
        green = int(color_start[1] + (color_end[1] - color_start[1]) * t)
        blue = int(color_start[2] + (color_end[2] - color_start[2]) * t)
        color = (red, green, blue)

        pygame.draw.line(GRADIENT_CACHED, color, (0, y), (WIDTH, y))
        
def draw_trajectory(screen, player, planets, steps=60, dt=0.5, color=(0, 255, 0)):
    trajectory_points, hit = predict_trajectory(player, planets, steps, dt)

    # Draw trajectory line with dots spaced every few points for clarity
    if hit:
        color =(255, 0, 0)
    
    for i in range(1, len(trajectory_points)):
        pygame.draw.line(screen, color, trajectory_points[i - 1], trajectory_points[i], 1)

    # Draw hollow ghost player at last predicted point
    if trajectory_points:
        ghost_x, ghost_y = trajectory_points[-1]
        rad_angle = math.radians(player.angle)

        front_x = ghost_x + 20 * math.cos(rad_angle)
        front_y = ghost_y - 20 * math.sin(rad_angle)
        left_x = ghost_x + 10 * math.cos(rad_angle + math.pi / 2)
        left_y = ghost_y - 10 * math.sin(rad_angle + math.pi / 2)
        right_x = ghost_x + 10 * math.cos(rad_angle - math.pi / 2)
        right_y = ghost_y - 10 * math.sin(rad_angle - math.pi / 2)
        pygame.draw.polygon(screen, color, [(front_x, front_y), (left_x, left_y), (right_x, right_y)], width=1)

        
# Simulation setup
show_title_screen()
planets = []
selected_planet = None
paused = False  # Add paused variable to control simulation state
player = Player(WIDTH // 2, HEIGHT // 2, 0, 15)


# Main loop
running = True
while running:
    if player.points != POINTS_PREV:
        POINTS_PREV = player.points
        player.mass = (player.points)/5**2
        draw_dynamic_gradient()
    #screen.fill(BLACK)
    screen.blit(GRADIENT_CACHED, (0, 0))

    if not paused:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.turn_left()
        if keys[pygame.K_RIGHT]:
            player.turn_right()
        if keys[pygame.K_UP]:
            player.move_forward()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Toggle pause state with the 'P' key
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not paused:
                player.shoot()
                player.points -= 2
            if event.key == pygame.K_p:
                paused = not paused  # Toggle pause state
            if event.key == pygame.K_q:  # Quit
                pygame.quit()
                running = False
                sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if event.button == 1:  # Left mouse button (for checking planets)
                # Check if the player clicked on a planet
                planet_clicked = False
                for planet in planets:
                    if planet.is_clicked(mouse_x, mouse_y):
                        selected_planet = planet
                        planet_clicked = True
                        break
                if not planet_clicked:
                    selected_planet = None  # Deselect any selected planet

            elif event.button == 3:  # Right mouse button (for creating a new planet)
                # If the player clicked on empty space, create a new planet
                if is_space_empty(mouse_x, mouse_y, planets):
                    planets.append(spawn_planet(mouse_x, mouse_y))
                else:
                    print("Clicked too close to an existing planet")

    # Spawn planets
    if not paused and len(planets) < MAX_PLANETS and random.random() < 5/TICK_RATE*TIME_SCALE:  # Expect number of planets = 5
        planets.append(spawn_planet())


    # Update planets if not paused
    if not paused: 
        player.offscreen()
        player.update(planets)        
        to_remove = set()  # Use a set to avoid duplicate removals
        for i, planet in enumerate(planets):
            if check_collision(player, planet) or player.points <= 0:
                if show_death_screen() == "restart":
                    reset_game()
                else:
                    pygame.quit()
                    sys.exit()
            for a, bullet in enumerate(player.bullets):
                if check_collision(bullet, planet):
                    del player.bullets[a]
                    new_planets = planet.split(bullet)  # Split the planet into smaller pieces
                    to_remove.add(i)  # Remove the original planet
                    planets.extend(new_planets)  # Add the new planets to the list
                    player.points += 10
            
            if i in to_remove:
                continue  # Skip already removed planets
            for j, other_planet in enumerate(planets):
                if i != j and j not in to_remove:
                    force = calculate_gravitational_force(planet, other_planet)
                    if force is None:
                        # Collision detected
                        if planet.mass / other_planet.mass > 1.25 or planet.mass / other_planet.mass < 0.8:
                            # Significant mass difference
                            i_momentum = [planet.mass * planet.velocity[0], planet.mass * planet.velocity[1]]
                            j_momentum = [other_planet.mass * other_planet.velocity[0], other_planet.mass * other_planet.velocity[1]]
                            new_momentum = [i_momentum[0] + j_momentum[0], i_momentum[1] + j_momentum[1]]
                            total_mass = planet.mass + other_planet.mass
                            velocity = [new_momentum[0] / total_mass, new_momentum[1] / total_mass]

                            if planet.mass > other_planet.mass:
                                planet.mass = total_mass
                                planet.velocity = velocity
                                planet.radius = ((planet.mass ** (3 / 4)) * PLANET_RADIUS_SCALE)
                                planet.glow_texture = create_glow_texture(int(planet.radius*3), planet.color, planet.mass)
                                to_remove.add(j)  # Remove the smaller planet
                            else:
                                other_planet.mass = total_mass
                                other_planet.velocity = velocity
                                other_planet.radius = ((other_planet.mass ** (3 / 4)) * PLANET_RADIUS_SCALE)
                                other_planet.glow_texture = create_glow_texture(int(other_planet.radius*3), other_planet.color, other_planet.mass)
                                to_remove.add(i)  # Remove the current planet
                            break
                        else:
                            to_remove.add(i)
                            to_remove.add(j)
                            break
                    else:
                        planet.velocity[0] += force[0] / planet.mass
                        planet.velocity[1] += force[1] / planet.mass

            if i not in to_remove:
                planet.update_position(TIME_SCALE)  # Update position with time scale
                if keys[pygame.K_LEFT] or keys[pygame.K_UP] or keys[pygame.K_RIGHT]: 
                    if not thrusting:
                        thrusting_sound.play(loops=-1)
                        thrusting = True
                else:
                    if thrusting:
                        thrusting_sound.stop()
                        thrusting = False
                if planet.is_offscreen():
                    to_remove.add(i)

        # Remove collided or off-screen planets
        planets = [planet for i, planet in enumerate(planets) if i not in to_remove]

    # Draw planets
    for planet in planets:
        planet.draw()
    draw_trajectory(screen, player, planets)
    player.draw(screen)

    points_window = pygame.Surface((170, 70), pygame.SRCALPHA)
    points_window.fill(TRANSLUCENT_WHITE)
    points_font = pygame.font.Font(None, 36)
    points_text = points_font.render(f"Points: {player.points:.0f}", True, TEXT_COLOR)

    points_window.blit(points_text, (10, 10))
    screen.blit(points_window, (0, 0))  # Adjust (50, 50) for position


    # If a planet is selected, display its stats
    if selected_planet:
        box_width = 320
        stats_window = pygame.Surface((box_width, 130), pygame.SRCALPHA)
        stats_window.fill(TRANSLUCENT_WHITE)

        mass_text = pygame.font.Font(None, 36).render(f"Mass: {selected_planet.mass:.2f}kg", True, TEXT_COLOR)
        velocity_text = pygame.font.Font(None, 36).render(f"Velocity: ({selected_planet.velocity[0]:.2f}, {selected_planet.velocity[1]:.2f})", True, TEXT_COLOR)
        name_text = pygame.font.Font(None, 36).render(f"Name: {selected_planet.name}", True, TEXT_COLOR)
        momentum_text = pygame.font.Font(None, 36).render(f"Momentum: ({selected_planet.velocity[0]/selected_planet.mass:.2f}, {selected_planet.velocity[1]/selected_planet.mass:.2f})", True, TEXT_COLOR)

        stats_window.blit(name_text, (10, 10))
        stats_window.blit(mass_text, (10, 40))
        stats_window.blit(velocity_text, (10, 70))
        stats_window.blit(momentum_text, (10, 100))

        screen.blit(stats_window, (WIDTH - box_width, 0))

    pygame.display.flip()
    clock.tick(TICK_RATE)

pygame.quit()