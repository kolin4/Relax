import pygame
import RPi.GPIO as GPIO
import time
import random
import sys

# GPIO setup
button_pins = [5, 6]
led_pins = [17, 27]
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
game_duration = 60
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

def game_loop():
    global score, stop_requested
    score = 0
    stop_requested = False
    countdown()
    start_ticks = pygame.time.get_ticks()
    current_led = None
    led_start_time = 0
    led_duration = 1000
    hit_window = False

    while True:
        screen.fill(WHITE)
        elapsed_ms = pygame.time.get_ticks() - start_ticks
        if elapsed_ms >= game_duration * 1000 or stop_requested:
            break

        time_left = max(0, game_duration - elapsed_ms / 1000)
        timer_text = f"{time_left:05.2f}s"
        draw_text(timer_text, 380, 10, digital_font, RED)
        draw_text(f"Score: {score}", 800, 100, small_font)
        draw_text(f"Level: {level}", 50, 100, small_font)

        stop_button_rect = pygame.Rect(870, 500, 130, 60)
        pygame.draw.rect(screen, RED, stop_button_rect, border_radius=8)
        stop_text = small_font.render("■ STOP", True, WHITE)
        screen.blit(stop_text, stop_text.get_rect(center=stop_button_rect.center))

        if not hit_window:
            current_led = random.randint(0, len(button_pins) - 1)
            GPIO.output(led_pins[current_led], True)
            led_start_time = pygame.time.get_ticks()
            hit_window = True

        elif pygame.time.get_ticks() - led_start_time > led_duration:
            GPIO.output(led_pins[current_led], False)
            hit_window = False

        if hit_window and GPIO.input(button_pins[current_led]) == GPIO.HIGH:
            GPIO.output(led_pins[current_led], False)
            score += 1
            hit_window = False
            time.sleep(0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if stop_button_rect.collidepoint(event.pos):
                    stop_requested = True

        pygame.display.update()
        clock.tick(60)

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

