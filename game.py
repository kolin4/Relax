import pygame
import RPi.GPIO as GPIO
import time
import random
import sys
import os

# GPIO setup
button_pin = 5  # jeden przycisk testowy
led_pin = 17    # odpowiadający LED
GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Użycie systemowego pull-up
GPIO.setup(led_pin, GPIO.OUT)
GPIO.output(led_pin, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("Button Test")

font = pygame.font.SysFont("Arial", 60)
small_font = pygame.font.SysFont("Arial", 40)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

score = 0
test_time = 10  # długość testu w sekundach

def draw_text(text, x, y, font, color=BLACK):
    rendered = font.render(text, True, color)
    screen.blit(rendered, (x, y))

def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_text(f"{i}", 380, 200, font)
        pygame.display.update()
        time.sleep(1)

def game_loop():
    global score
    score = 0
    countdown()

    start_time = time.time()
    reaction_window = False
    led_on_time = 0

    while time.time() - start_time < test_time:
        screen.fill(WHITE)
        draw_text(f"Score: {score}", 50, 30, small_font)
        draw_text(f"Time Left: {max(0, int(test_time - (time.time() - start_time)))}s", 500, 30, small_font)

        # Jeśli LED zgasł, zapal go ponownie co losowy czas
        if not reaction_window:
            time.sleep(random.uniform(1, 2.5))  # losowa przerwa
            GPIO.output(led_pin, True)
            led_on_time = time.time()
            reaction_window = True

        if reaction_window:
            if GPIO.input(button_pin) == GPIO.LOW:  # przycisk wciśnięty (PUD_UP = LOW po naciśnięciu)
                GPIO.output(led_pin, False)
                score += 1
                reaction_window = False
                time.sleep(0.3)  # krótki debounce
            elif time.time() - led_on_time > 1.0:  # zbyt wolna reakcja
                GPIO.output(led_pin, False)
                reaction_window = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()

        pygame.display.update()
        clock.tick(60)

    screen.fill(WHITE)
    draw_text("Test complete!", 250, 180, font)
    draw_text(f"Score: {score}", 300, 260, font)
    pygame.display.update()
    time.sleep(5)

try:
    game_loop()
except KeyboardInterrupt:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
