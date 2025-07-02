import pygame
import RPi.GPIO as GPIO
import time
import random
import sys

# GPIO setup
button_pins = [5, 6]       # GPIOs for 2 buttons
led_pins = [17, 27]        # GPIOs for 2 LEDs
GPIO.setmode(GPIO.BCM)

for bp in button_pins:
    GPIO.setup(bp, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

for lp in led_pins:
    GPIO.setup(lp, GPIO.OUT)
    GPIO.output(lp, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester")

# Font setup
try:
    digital_font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 80)
except:
    digital_font = pygame.font.SysFont("Courier", 80)

font = pygame.font.SysFont("Arial", 60)
small_font = pygame.font.SysFont("Arial", 40)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
RED = (200, 0, 0)
BLACK = (0, 0, 0)

level = 1
score = 0
game_duration = 60  # seconds
stop_requested = False

def draw_text(text, x, y, font, color=BLACK):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))

def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_text(f"{i}", 480, 250, font)
        pygame.display.update()
        time.sleep(1)

def light_up_button(index, led_time=1.0):
    GPIO.output(led_pins[index], True)
    start = time.time()
    while time.time() - start < led_time:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
        if GPIO.input(button_pins[index]) == GPIO.HIGH:
            GPIO.output(led_pins[index], False)
            return True
        time.sleep(0.01)
    GPIO.output(led_pins[index], False)
    return False

def game_loop():
    global score, stop_requested
    score = 0
    stop_requested = False
    countdown()
    start_time = time.time()

    while time.time() - start_time < game_duration:
        elapsed = time.time() - start_time
        if stop_requested:
            break

        screen.fill(WHITE)
        time_left = max(0, game_duration - elapsed)
        timer_text = f"{time_left:05.2f}s"
        draw_text(timer_text, 412, 20, digital_font, RED)
        draw_text(f"Score: {score}", 800, 100, small_font)
        draw_text(f"Level: {level}", 50, 100, small_font)
        draw_text("■ STOP", 880, 500, small_font)

        pygame.draw.rect(screen, RED, (860, 490, 140, 60), border_radius=8)

        pygame.display.update()

        index = random.randint(0, len(button_pins) - 1)
        hit = light_up_button(index)
        if hit:
            score += 1
        time.sleep(0.2)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(860, 490, 140, 60).collidepoint(event.pos):
                    stop_requested = True

    screen.fill(WHITE)
    draw_text("GAME STOPPED!" if stop_requested else "TIME'S UP!", 340, 200, font)
    draw_text(f"Final Score: {score}", 360, 300, font)
    pygame.display.update()
    time.sleep(5)

def menu():
    global level
    while True:
        screen.fill(WHITE)

        draw_text("Level", 470, 100, small_font)

        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x, 150, 120, 80)
            color = GREEN if level == i + 1 else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=12)
            draw_text(str(i + 1), x + 40, 160, small_font)

        pygame.draw.rect(screen, BLUE, (312, 400, 180, 80), border_radius=12)
        pygame.draw.rect(screen, GRAY, (532, 400, 220, 80), border_radius=12)
        draw_text("▶ START", 330, 410, small_font)
        draw_text("🏆 Highscores", 540, 410, small_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for i in range(5):
                    if pygame.Rect(100 + i * 170, 150, 120, 80).collidepoint(x, y):
                        level = i + 1
                if pygame.Rect(312, 400, 180, 80).collidepoint(x, y):
                    game_loop()

        pygame.display.update()
        clock.tick(30)

try:
    menu()
except KeyboardInterrupt:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()

