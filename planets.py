import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 1536, 864
GRAVITY_CONSTANT = 10
PLANET_RADIUS_SCALE = 1.5
MAX_PLANETS = 6
TICK_RATE = 60
MAX_GLOW_RADIUS = 100  # Maximum radius of the glow effect
GLOW_TEXTURE_RADIUS = 60  # Reduced radius for optimized glow texture
TIME_SCALE = 0.5  # Time scale factor (default 1 is normal speed, less than 1 slows it down)

# Colors
BLACK = (0, 0, 0)
TRANSLUCENT_WHITE = (255, 255, 255, 128)  # Semi-transparent white
TEXT_COLOR = (255, 255, 255)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Simulation")
clock = pygame.time.Clock()

# Load glow texture (a radial gradient image)
def create_glow_texture(radius, color):
    glow_texture = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for x in range(-radius, radius):
        for y in range(-radius, radius):
            dist = math.sqrt(x**2 + y**2)
            if dist < radius:
                intensity = max(0, 255 - (dist / radius) * 255)
                glow_color = (
                    min(int(color[0] + intensity), 255),
                    min(int(color[1] + intensity), 255),
                    min(int(color[2] + intensity), 255),
                    int(intensity)
                )
                glow_texture.set_at((x + radius, y + radius), glow_color)
    return glow_texture

# Planet class
class Planet:
    def __init__(self, x, y, mass, velocity, color):
        self.x = x
        self.y = y
        self.mass = mass
        self.velocity = velocity
        self.radius = int((mass ** (3/4)) * PLANET_RADIUS_SCALE)
        self.color = color
        self.glow_texture = create_glow_texture(GLOW_TEXTURE_RADIUS, self.color)
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

    # Add random variation to the initial velocity, introducing a bias in direction
    angle_bias = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle bias between -45 and 45 degrees
    velocity = [
        (WIDTH / 2 - x) * 0.005 * math.cos(angle_bias) + random.uniform(-0.5, 0.5),
        (HEIGHT / 2 - y) * 0.005 * math.sin(angle_bias) + random.uniform(-0.5, 0.5),
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

# Simulation setup
planets = []
selected_planet = None
paused = False  # Add paused variable to control simulation state

# Main loop
running = True
while running:
    screen.fill(BLACK)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Toggle pause state with the 'P' key
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused  # Toggle pause state
            elif event.key == pygame.K_UP:
                TIME_SCALE += 0.1  # Increase time scale (faster)
            elif event.key == pygame.K_DOWN:
                TIME_SCALE = max(0.01, TIME_SCALE - 0.1)  # Decrease time scale (slower)
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
        to_remove = set()  # Use a set to avoid duplicate removals
        for i, planet in enumerate(planets):
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

                            print(f"Planet 1 Mass: {planet.mass}, Velocity: {planet.velocity}, Momentum: ({i_momentum[0]}, {i_momentum[1]})")
                            print(f"Planet 2 Mass: {other_planet.mass}, Velocity: {other_planet.velocity}, Momentum: ({j_momentum[0]}, {j_momentum[1]})")
                            print(f"Total Mass: {total_mass}, Final Velocity: ({velocity[0]}, {velocity[1]}), Momentum: ({new_momentum[0]}, {new_momentum[1]})")

                            if planet.mass > other_planet.mass:
                                planet.mass = total_mass
                                planet.velocity = velocity
                                planet.radius = ((planet.mass ** (3 / 4)) * PLANET_RADIUS_SCALE)
                                to_remove.add(j)  # Remove the smaller planet
                            else:
                                other_planet.mass = total_mass
                                other_planet.velocity = velocity
                                other_planet.radius = ((other_planet.mass ** (3 / 4)) * PLANET_RADIUS_SCALE)
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
                if planet.is_offscreen():
                    to_remove.add(i)

        # Remove collided or off-screen planets
        planets = [planet for i, planet in enumerate(planets) if i not in to_remove]

    # Draw planets
    for planet in planets:
        planet.draw()

    # If a planet is selected, display its stats
    if selected_planet:
        stats_window = pygame.Surface((320, 130), pygame.SRCALPHA)
        stats_window.fill(TRANSLUCENT_WHITE)

        mass_text = pygame.font.Font(None, 36).render(f"Mass: {selected_planet.mass:.2f}kg", True, TEXT_COLOR)
        velocity_text = pygame.font.Font(None, 36).render(f"Velocity: ({selected_planet.velocity[0]:.2f}, {selected_planet.velocity[1]:.2f})", True, TEXT_COLOR)
        name_text = pygame.font.Font(None, 36).render(f"Name: {selected_planet.name}", True, TEXT_COLOR)
        momentum_text = pygame.font.Font(None, 36).render(f"Momentum: ({selected_planet.velocity[0]/selected_planet.mass:.2f}, {selected_planet.velocity[1]/selected_planet.mass:.2f})", True, TEXT_COLOR)

        stats_window.blit(name_text, (10, 10))
        stats_window.blit(mass_text, (10, 40))
        stats_window.blit(velocity_text, (10, 70))
        stats_window.blit(momentum_text, (10, 100))

        screen.blit(stats_window, (WIDTH - 330, 20))

    pygame.display.flip()
    clock.tick(TICK_RATE)

pygame.quit()