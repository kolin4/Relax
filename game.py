import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((1024, 600))  # Fullscreen DSI display
pygame.display.set_caption("Reaction Tester")
font = pygame.font.SysFont("Arial", 40)
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)
BLACK = (0, 0, 0)

# Selected difficulty
level = 1

def draw_button(label, rect, color):
    pygame.draw.rect(screen, color, rect, border_radius=12)
    text = font.render(label, True, BLACK)
    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)

def menu():
    global level
    while True:
        screen.fill(WHITE)


        # "Level" label
        level_label = font.render("Level", True, BLACK)
        screen.blit(level_label, (470, 130))  # center over buttons

        # Draw level buttons (1 to 5)
        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x, 200, 120, 80)
            color = GREEN if level == i + 1 else GRAY
            draw_button(str(i + 1), rect, color)

        # Draw START button
        draw_button("START", pygame.Rect(312, 400, 180, 80), BLUE)
        draw_button("🏆 Highscores", pygame.Rect(532, 400, 220, 80), GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i in range(5):
                    if pygame.Rect(100 + i * 170, 200, 120, 80).collidepoint(x, y):
                        level = i + 1
                if pygame.Rect(412, 400, 180, 80).collidepoint(x, y):
                    print("START! Selected level:", level)
                    return level  # proceed to game loop

        pygame.display.update()
        clock.tick(30)

# Launch menu
menu()
