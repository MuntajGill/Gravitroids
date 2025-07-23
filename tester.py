import pygame
import random
import math
import sys
from multiprocessing import Pool, Manager

# Constants
WIDTH, HEIGHT = 1536, 864
GRAVITY_CONSTANT = 10
PLANET_RADIUS_SCALE = 1.5
MAX_PLANETS = 6
TICK_RATE = 60
TIME_SCALE = 0.5
BULLET_SPEED = 8
MAX_PLAYER_SPEED = 4
MAX_BULLETS = 50
BLACK = (0, 0, 0)
TRANSLUCENT_WHITE = (255, 255, 255, 128)
TEXT_COLOR = (255, 255, 255)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Simulation")
clock = pygame.time.Clock()

class Player:
    def __init__(self, x, y, angle, radius):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = 0
        self.vy = 0
        self.radius = radius
        self.bullets = []

    def update_position(self):
        self.x += self.vx
        self.y += self.vy

class Planet:
    def __init__(self, x, y, mass, velocity):
        self.x = x
        self.y = y
        self.mass = mass
        self.velocity = velocity
        self.radius = int((mass ** (3/4)) * PLANET_RADIUS_SCALE)

    def update_position(self):
        self.x += self.velocity[0] * TIME_SCALE
        self.y += self.velocity[1] * TIME_SCALE

# Helper function for gravitational force calculations
def calculate_gravitational_force(args):
    planet1, planet2 = args
    dx = planet2.x - planet1.x
    dy = planet2.y - planet1.y
    distance = math.sqrt(dx**2 + dy**2)
    if distance <= planet1.radius + planet2.radius:
        return None  # Collision
    force = GRAVITY_CONSTANT * planet1.mass * planet2.mass / distance**2
    angle = math.atan2(dy, dx)
    return (force * math.cos(angle), force * math.sin(angle))

def update_planet(args):
    planet, forces = args
    for fx, fy in forces:
        planet.velocity[0] += fx / planet.mass
        planet.velocity[1] += fy / planet.mass
    planet.update_position()
    return planet

# Main game logic
planets = [Planet(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100), random.uniform(5, 50), [random.uniform(-1, 1), random.uniform(-1, 1)]) for _ in range(MAX_PLANETS)]
player = Player(WIDTH // 2, HEIGHT // 2, 0, 15)
manager = Manager()
pool = Pool()

running = True
while running:
    screen.fill(BLACK)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Gravitational force calculations
    force_tasks = [(planet1, planet2) for i, planet1 in enumerate(planets) for j, planet2 in enumerate(planets) if i != j]
    forces = pool.map(calculate_gravitational_force, force_tasks)

    # Organize forces by planet
    planet_forces = [manager.list() for _ in planets]
    for idx, force in enumerate(forces):
        if force is not None:
            planet1_idx = idx // (len(planets) - 1)
            planet_forces[planet1_idx].append(force)

    # Update planet positions
    planet_tasks = [(planet, planet_forces[i]) for i, planet in enumerate(planets)]
    planets = pool.map(update_planet, planet_tasks)

    # Draw planets
    for planet in planets:
        pygame.draw.circle(screen, (255, 255, 255), (int(planet.x), int(planet.y)), planet.radius)

    pygame.display.flip()
    clock.tick(TICK_RATE)

pygame.quit()
pool.close()
