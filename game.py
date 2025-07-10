import pygame
import RPi.GPIO as GPIO
import time
import random
import sys
import os
import json

# GPIO setup
button_pins = [5, 6]  # Two buttons
led_pins = [17, 27]   # Two LEDs
GPIO.setmode(GPIO.BCM)
for bp in button_pins:
    GPIO.setup(bp, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for lp in led_pins:
    GPIO.setup(lp, GPIO.OUT)
    GPIO.output(lp, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
RED = (200, 0, 0)
BLACK = (0, 0, 0)

# Game state
level = 1
score = 0
game_duration = 60
stop_requested = False
highscore_visible = False
show_keyboard = False
name_input = ""

# Timing per level
LEVEL_TIMINGS = {
    1: 1000,
    2: 900,
    3: 800,
    4: 500,
    5: 300
}

# Ensure score directory exists
if not os.path.exists("wyniki"):
    os.makedirs("wyniki")

def load_scores(level):
    path = f"wyniki/level_{level}.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def save_score(level, name, score):
    scores = load_scores(level)
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    with open(f"wyniki/level_{level}.json", 'w') as f:
        json.dump(scores, f)

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

def draw_keyboard():
    global name_input
    keys = [
        "ABCDEF",
        "GHIJKL",
        "MNOPQR",
        "STUVWX",
        "YZ <- OK"
    ]
    for row_idx, row in enumerate(keys):
        for col_idx, char in enumerate(row):
            rect = pygame.Rect(60 + col_idx * 140, 150 + row_idx * 80, 120, 60)
            pygame.draw.rect(screen, GRAY, rect)
            draw_text(char, rect.x + 30, rect.y + 10, small_font)

def handle_keyboard_click(pos):
    global name_input, show_keyboard
    x, y = pos
    row = (y - 150) // 80
    col = (x - 60) // 140
    keys = [
        "ABCDEF",
        "GHIJKL",
        "MNOPQR",
        "STUVWX",
        "YZ <- OK"
    ]
    if 0 <= row < len(keys) and 0 <= col < len(keys[row]):
        key = keys[row][col]
        if key == "<":
            name_input = name_input[:-1]
        elif key == "O":
            if len(name_input) > 0:
                save_score(level, name_input, score)
                name_input = ""
                show_keyboard = False
        elif len(key) == 1 and len(name_input) < 10:
            name_input += key

def game_loop():
    global score, stop_requested, level, show_keyboard
    score = 0
    stop_requested = False
    countdown()

    led_time = LEVEL_TIMINGS.get(level, 1000)

    start_time = pygame.time.get_ticks()
    current_led = None
    led_on = False
    led_start = 0
    next_led_time = start_time + led_time

    while not stop_requested:
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - start_time) / 1000
        if elapsed >= game_duration:
            break

        screen.fill(WHITE)
        draw_text(f"Score: {score}", 50, 30, medium_font)
        draw_text(f"Time: {game_duration - elapsed:05.2f}s", 650, 30, medium_font)
        draw_text(f"Level: {level}", 400, 30, medium_font)

        if not led_on and current_time >= next_led_time:
            current_led = random.randint(0, 1)
            GPIO.output(led_pins[current_led], True)
            led_on = True
            led_start = current_time

        if led_on and current_time - led_start >= led_time:
            GPIO.output(led_pins[current_led], False)
            led_on = False
            next_led_time = current_time + led_time

        if led_on:
            for i, pin in enumerate(button_pins):
                if GPIO.input(pin) == GPIO.LOW:
                    if i == current_led:
                        score += 1
                    else:
                        score -= 1
                    GPIO.output(led_pins[current_led], False)
                    led_on = False
                    next_led_time = current_time + led_time

        stop_button_rect = pygame.Rect(800, 500, 200, 80)
        pygame.draw.rect(screen, RED, stop_button_rect)
        draw_text("■ STOP", 830, 520, small_font, WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if stop_button_rect.collidepoint(event.pos):
                    stop_requested = True

        pygame.display.update()
        clock.tick(60)

    for lp in led_pins:
        GPIO.output(lp, False)

    screen.fill(WHITE)
    draw_centered_text("KONIEC", 220, font)
    draw_centered_text(f"Twój wynik: {score}", 320, font)
    pygame.display.update()
    time.sleep(2)

    top_scores = load_scores(level)
    if len(top_scores) < 10 or score > top_scores[-1]["score"]:
        show_keyboard = True
        while show_keyboard:
            screen.fill(WHITE)
            draw_centered_text("Nowy wynik! Podaj imię:", 80, small_font)
            draw_centered_text(name_input, 160, font)
            draw_keyboard()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    show_keyboard = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    handle_keyboard_click(event.pos)
            pygame.display.update()
            clock.tick(30)

def draw_highscores():
    scores = load_scores(level)
    screen.fill(WHITE)
    draw_centered_text(f"Top 10 - Level {level}", 50, medium_font)
    for i, entry in enumerate(scores):
        draw_text(f"{i+1}. {entry['name']} - {entry['score']}", 300, 130 + i * 40, small_font)
    close_button = pygame.Rect(950, 10, 50, 50)
    pygame.draw.rect(screen, RED, close_button)
    draw_text("X", 960, 10, small_font, WHITE)
    return close_button

def menu():
    global level, highscore_visible
    while True:
        screen.fill(WHITE)
        draw_centered_text("Wybierz poziom", 80, medium_font)

        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x, 150, 120, 80)
            color = GREEN if level == i + 1 else GRAY
            pygame.draw.rect(screen, color, rect, border_radius=12)
            draw_text(str(i + 1), x + 45, 165, medium_font)

        start_button_rect = pygame.Rect(300, 400, 300, 90)
        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        draw_text("▶ START", 320, 420, small_font, WHITE)

        highscore_button_rect = pygame.Rect(620, 400, 150, 90)
        pygame.draw.rect(screen, GRAY, highscore_button_rect, border_radius=12)
        draw_text("Highscore", 630, 420, small_font, BLACK)

        if highscore_visible:
            close_btn = draw_highscores()
        else:
            close_btn = None

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
                if highscore_button_rect.collidepoint(x, y):
                    highscore_visible = True
                if close_btn and close_btn.collidepoint(x, y):
                    highscore_visible = False

        pygame.display.update()
        clock.tick(30)

try:
    menu()
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
