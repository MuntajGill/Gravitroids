import pygame
pygame.init()
pygame.mixer.init()

# Set up display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Sound Test")

# Load sound
click_sound = pygame.mixer.Sound("sounds/shoot.ogg")
click_sound.set_volume(0.5)  # Range: 0.0 (silent) to 1.0 (max)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Play sound on mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_sound.play()

    screen.fill((0, 0, 0))
    pygame.display.flip()

pygame.quit()
