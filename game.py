import pygame
import RPi.GPIO as GPIO
import time
import sys
import random

# GPIO config
BUTTON_PINS = [5, 6]     # Two buttons
LED_PINS = [17, 27]      # Two LEDs
GPIO.setmode(GPIO.BCM)
for pin in BUTTON_PINS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in LED_PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("2-Button Reaction Tester")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 180, 0)
GRAY = (180, 180, 180)

score = 0
game_duration = 60
stop_requested = False
level = 1  # default level

# Generate level settings: {level: (LED on duration, interval duration)}
LEVEL_SETTINGS = {lvl: (1000 - (lvl - 1) * 100, 1000 - (lvl - 1) * 100) for lvl in range(1, 6)}


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

    led_duration, led_interval = LEVEL_SETTINGS[level]

    start_time = pygame.time.get_ticks()
    led_on = False
    led_start = 0
    current_led = 0
    next_led = start_time + led_interval

    while not stop_requested:
        now = pygame.time.get_ticks()
        elapsed = (now - start_time) / 1000
        if elapsed >= game_duration:
            break

        screen.fill(WHITE)
        draw_text(f"Score: {score}", 50, 30, medium_font)
        draw_text(f"Time: {game_duration - elapsed:05.2f}s", 600, 30, medium_font)

        # LED ON logic
        if not led_on and now >= next_led:
            current_led = random.randint(0, 1)
            GPIO.output(LED_PINS[current_led], True)
            led_start = now
            led_on = True

        # LED OFF after duration
        if led_on and now - led_start > led_duration:
            GPIO.output(LED_PINS[current_led], False)
            led_on = False
            next_led = now + led_interval

        # Button check
        if led_on and GPIO.input(BUTTON_PINS[current_led]) == GPIO.LOW:
            score += 1
            GPIO.output(LED_PINS[current_led], False)
            led_on = False
            next_led = now + led_interval
            debounce_until = pygame.time.get_ticks() + 200
            while pygame.time.get_ticks() < debounce_until:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        stop_requested = True
                clock.tick(60)

        # STOP button
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
            draw_centered_text(str(i + 1), 190, small_font, BLACK)

        start_button_rect = pygame.Rect(300, 400, 400, 100)
        pygame.draw.rect(screen, RED, start_button_rect, border_radius=12)
        draw_centered_text("▶ START", 450, medium_font, WHITE)

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
