import pygame
import RPi.GPIO as GPIO
import time
import sys
import random

# GPIO config
BUTTON_PIN = 5
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # PUD_UP, aktywacja przy LOW
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("1-Button Reaction Tester")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)

score = 0
game_duration = 60
stop_requested = False

def draw_text(text, x, y, font, color=BLACK):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_centered_text(text, y, font, color=BLACK):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(512, y))
    screen.blit(surface, rect)

def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_centered_text(str(i), 300, font)
        pygame.display.update()
        time.sleep(1)

def game_loop():
    global score, stop_requested
    score = 0
    stop_requested = False
    countdown()

    start_time = pygame.time.get_ticks()
    led_on = False
    led_start = 0
    next_led_time = start_time + random.randint(1000, 3000)

    while not stop_requested:
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - start_time) / 1000
        if elapsed >= game_duration:
            break

        screen.fill(WHITE)
        draw_text(f"Score: {score}", 50, 30, medium_font)
        draw_text(f"Time: {game_duration - elapsed:05.2f}s", 650, 30, medium_font)

        # Obsługa LED
        if not led_on and current_time >= next_led_time:
            GPIO.output(LED_PIN, True)
            led_on = True
            led_start = current_time

        if led_on and current_time - led_start > 1000:
            GPIO.output(LED_PIN, False)
            led_on = False
            next_led_time = current_time + random.randint(1000, 2500)

        # Sprawdzenie przycisku
        if led_on and GPIO.input(BUTTON_PIN) == GPIO.LOW:
            score += 1
            GPIO.output(LED_PIN, False)
            led_on = False
            next_led_time = current_time + random.randint(1000, 2500)
            time.sleep(200 / 1000)  # debounce

        # Obsługa przycisku STOP
        stop_button_rect = pygame.Rect(800, 500, 200, 80)
        pygame.draw.rect(screen, RED, stop_button_rect)
        draw_centered_text("■ STOP", 540, small_font, WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if stop_button_rect.collidepoint(event.pos):
                    stop_requested = True

        pygame.display.update()
        clock.tick(60)

    GPIO.output(LED_PIN, False)
    screen.fill(WHITE)
    draw_centered_text("KONIEC", 220, font)
    draw_centered_text(f"Twój wynik: {score}", 320, font)
    pygame.display.update()
    time.sleep(5)

try:
    game_loop()
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
