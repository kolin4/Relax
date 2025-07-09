import pygame
import RPi.GPIO as GPIO
import time
import random
import sys

# GPIO setup – jeden przycisk i jedna dioda
button_pin = 5
led_pin = 17
GPIO.setmode(GPIO.BCM)

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led_pin, GPIO.OUT)
GPIO.output(led_pin, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester")

try:
    digital_font = pygame.font.Font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 110)
except:
    digital_font = pygame.font.SysFont("Courier", 110)

font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 60)
small_font = pygame.font.SysFont("Arial", 45)
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

def draw_centered_text(text, rect, font, color=WHITE):
    rendered = font.render(text, True, color)
    text_rect = rendered.get_rect(center=rect.center)
    screen.blit(rendered, text_rect)

def draw_centered_screen_text(text, y_offset, font, color=BLACK):
    rendered = font.render(text, True, color)
    text_rect = rendered.get_rect(center=(1024 // 2, y_offset))
    screen.blit(rendered, text_rect)

def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_centered_screen_text(f"{i}", 300, font)
        pygame.display.update()
        time.sleep(1)

def game_loop():
    global score, stop_requested
    score = 0
    stop_requested = False
    countdown()
    start_ticks = pygame.time.get_ticks()
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
        rendered_timer = digital_font.render(timer_text, True, RED)
        timer_rect = rendered_timer.get_rect(center=(512, 70))
        screen.blit(rendered_timer, timer_rect)

        draw_text(f"Level: {level}", 50, 30, medium_font)
        draw_text(f"Score: {score}", 760, 30, medium_font)

        stop_button_rect = pygame.Rect(800, 500, 200, 80)
        pygame.draw.rect(screen, RED, stop_button_rect, border_radius=8)
        draw_centered_text("■ STOP", stop_button_rect, small_font)

        # LED zapalany co losowy czas
        if not hit_window:
            time.sleep(random.uniform(1.0, 2.5))
            GPIO.output(led_pin, True)
            led_start_time = pygame.time.get_ticks()
            hit_window = True

        elif pygame.time.get_ticks() - led_start_time > led_duration:
            GPIO.output(led_pin, False)
            hit_window = False

        if hit_window and GPIO.input(button_pin) == GPIO.HIGH:
            GPIO.output(led_pin, False)
            score += 1
            hit_window = False
            time.sleep(0.2)

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
    draw_centered_screen_text("GAME STOPPED!" if stop_requested else "TIME'S UP!", 200, font)
    draw_centered_screen_text(f"Final Score: {score}", 300, font)
    pygame.display.update()
    time.sleep(5)

def draw_text(text, x, y, font, color=BLACK):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))

def menu():
    global level
    while True:
        screen.fill(WHITE)
        draw_centered_screen_text("Level", 80, medium_font)

        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x, 150, 120, 80)
            color = GREEN if level == i + 1 else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=12)
            draw_centered_text(str(i + 1), rect, small_font, BLACK)

        start_button_rect = pygame.Rect(270, 400, 250, 90)
        highscores_button_rect = pygame.Rect(540, 400, 270, 90)
        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        pygame.draw.rect(screen, GRAY, highscores_button_rect, border_radius=12)
        draw_centered_text("▶ START", start_button_rect, small_font)
        draw_centered_text("🏆 Highscores", highscores_button_rect, small_font)

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
                if start_button_rect.collidepoint(x, y):
                    game_loop()

        pygame.display.update()
        clock.tick(30)

try:
    menu()
except KeyboardInterrupt:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
