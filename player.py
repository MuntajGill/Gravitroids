import pygame
import math

# Constants
WIDTH, HEIGHT = 800, 600
TICK_RATE = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BULLET_SPEED = 8  # Increased bullet speed
MAX_PLAYER_SPEED = 4
MAX_BULLETS = 5

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED

    def update(self):
        rad_angle = math.radians(self.angle)
        self.x += self.speed * math.cos(rad_angle)
        self.y -= self.speed * math.sin(rad_angle)  # Negative because Pygame's y-axis is inverted

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5)

class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle  # In degrees
        self.vx = 0  # Velocity in the x direction
        self.vy = 0  # Velocity in the y direction
        self.max_speed = MAX_PLAYER_SPEED
        self.acceleration = 0.1  # Acceleration
        self.bullets = []
        self.is_moving = False  # To track if the player is holding the move button

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

    def update(self):
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

        pygame.draw.polygon(screen, WHITE, [(front_x, front_y), (left_x, left_y), (right_x, right_y)])

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Player Movement and Shooting Test")
clock = pygame.time.Clock()

# Create a player instance
player = Player(WIDTH // 2, HEIGHT // 2, 0)

# Main loop
running = True
while running:
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # Player controls (keep moving when keys are held)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.turn_left()
    if keys[pygame.K_RIGHT]:
        player.turn_right()
    if keys[pygame.K_UP]:
        player.move_forward()

    # Update player state
    player.update()

    # Draw player
    player.draw(screen)

    pygame.display.flip()
    clock.tick(TICK_RATE)

pygame.quit()