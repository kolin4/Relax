import pygame
import RPi.GPIO as GPIO
import time
import sys
import random

# GPIO config
BUTTON_PINS = [5, 6]
LED_PINS = [17, 27]
GPIO.setmode(GPIO.BCM)
for pin in BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)

score = 0
game_duration = 60
stop_requested = False
level = 1

LEVEL_SETTINGS = {
    1: 1.0,
    2: 0.9,
    3: 0.8,
    4: 0.7,
    5: 0.6
}

def draw_text(text, x, y, font, color=BLACK):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_centered_text(text, y, font, color=BLACK):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(512, y))
    screen.blit(surface, rect)

def draw_centered_in_rect(text, rect, font, color=WHITE):
    surface = font.render(text, True, color)
    text_rect = surface.get_rect(center=rect.center)
    screen.blit(surface, text_rect)

def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_centered_text(str(i), 300, font)
        pygame.display.update()
        time.sleep(1)

def game_loop():
    global score, stop_requested, level
    score = 0
    stop_requested = False
    countdown()

    led_time = LEVEL_SETTINGS.get(level, 1.0)
    pause_time = led_time

    start_time = time.time()
    led_on = False
    led_start = 0
    next_led_time = start_time + random.uniform(1, 2.5)
    current_led = None

    while not stop_requested:
        current_time = time.time()
        elapsed = current_time - start_time
        if elapsed >= game_duration:
            break

        screen.fill(WHITE)
        draw_text(f"Score: {score}", 50, 30, medium_font)
        draw_text(f"Time: {game_duration - elapsed:05.2f}s", 650, 30, medium_font)
        draw_text(f"Level: {level}", 420, 30, medium_font)

        # LED logic
        if not led_on and current_time >= next_led_time:
            current_led = random.randint(0, 1)
            GPIO.output(LED_PINS[current_led], True)
            led_on = True
            led_start = current_time

        if led_on and current_time - led_start > led_time:
            GPIO.output(LED_PINS[current_led], False)
            led_on = False
            next_led_time = current_time + pause_time
            current_led = None

        # Check button input
        for i, btn_pin in enumerate(BUTTON_PINS):
            if GPIO.input(btn_pin) == GPIO.LOW:
                if led_on:
                    if i == current_led:
                        score += 1
                    else:
                        score = max(0, score - 1)
                    GPIO.output(LED_PINS[current_led], False)
                    led_on = False
                    next_led_time = current_time + pause_time
                time.sleep(0.2)  # debounce

        # STOP button
        stop_button_rect = pygame.Rect(800, 500, 200, 80)
        pygame.draw.rect(screen, RED, stop_button_rect)
        draw_centered_in_rect("■ STOP", stop_button_rect, small_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if stop_button_rect.collidepoint(event.pos):
                    stop_requested = True

        pygame.display.update()
        clock.tick(60)

    for pin in LED_PINS:
        GPIO.output(pin, False)

    screen.fill(WHITE)
    draw_centered_text("KONIEC", 220, font)
    draw_centered_text(f"Twój wynik: {score}", 320, font)
    pygame.display.update()
    time.sleep(5)

def menu():
    global level
    while True:
        screen.fill(WHITE)
        draw_centered_text("Wybierz poziom", 80, medium_font)

        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x, 150, 120, 80)
            color = GREEN if level == i + 1 else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=12)
            draw_centered_in_rect(str(i + 1), rect, small_font, BLACK)

        start_button_rect = pygame.Rect(380, 400, 250, 90)
        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        draw_centered_in_rect("▶ START", start_button_rect, small_font)

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
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
