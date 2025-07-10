
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

# Timing per level
LEVEL_TIMINGS = {
    1: 1000,
    2: 900,
    3: 800,
    4: 500,
    5: 300
}

# Highscore data
HIGHSCORE_DIR = "wyniki"
os.makedirs(HIGHSCORE_DIR, exist_ok=True)

def get_highscore_file(level):
    return os.path.join(HIGHSCORE_DIR, f"level_{level}.json")

def load_highscores(level):
    path = get_highscore_file(level)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_highscores(level, scores):
    path = get_highscore_file(level)
    with open(path, "w") as f:
        json.dump(scores, f)

def add_score(level, name, score):
    scores = load_highscores(level)
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    save_highscores(level, scores)

def draw_text(text, x, y, font, color=BLACK):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_centered_text(text, y, font, color=BLACK):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(512, y))
    screen.blit(surface, rect)

def draw_keyboard(name_input):
    screen.fill(WHITE)
    draw_centered_text("Wpisz swoje imię", 50, medium_font)
    draw_centered_text(name_input, 120, font)

    keys = [
        "A B C D E F G H I J",
        "K L M N O P Q R S T",
        "U V W X Y Z . < OK"
    ]

    key_w, key_h = 80, 80
    spacing = 10
    start_x = (1024 - (key_w + spacing) * 10 + spacing) // 2
    start_y = 180

    for row_idx, row in enumerate(keys):
        for col_idx, char in enumerate(row.split()):
            rect = pygame.Rect(
                start_x + col_idx * (key_w + spacing),
                start_y + row_idx * (key_h + spacing),
                key_w, key_h
            )
            pygame.draw.rect(screen, GRAY, rect, border_radius=8)
            draw_centered_text(char, rect.centery - 20, small_font, BLACK)

def get_name_input():
    name = ""
    while True:
        draw_keyboard(name)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                keys = [
                    "A B C D E F G H I J",
                    "K L M N O P Q R S T",
                    "U V W X Y Z . < OK"
                ]
                key_w, key_h = 80, 80
                spacing = 10
                start_x = (1024 - (key_w + spacing) * 10 + spacing) // 2
                start_y = 180
                for row_idx, row in enumerate(keys):
                    for col_idx, char in enumerate(row.split()):
                        rect = pygame.Rect(
                            start_x + col_idx * (key_w + spacing),
                            start_y + row_idx * (key_h + spacing),
                            key_w, key_h
                        )
                        if rect.collidepoint(x, y):
                            if char == "<":
                                name = name[:-1]
                            elif char == "OK":
                                return name[:10]
                            else:
                                name += char
        clock.tick(30)

def show_highscores():
    scores = load_highscores(level)
    viewing = True
    while viewing:
        screen.fill(WHITE)
        draw_centered_text(f"TOP 10 - Poziom {level}", 60, font)
        for i, entry in enumerate(scores):
            draw_text(f"{i+1}. {entry['name']}: {entry['score']}", 300, 140 + i * 40, small_font)

        close_btn = pygame.Rect(960, 20, 40, 40)
        pygame.draw.rect(screen, RED, close_btn, border_radius=5)
        draw_text("X", 970, 20, small_font, WHITE)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if close_btn.collidepoint(event.pos):
                    viewing = False

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

    scores = load_highscores(level)
    if len(scores) < 10 or score > scores[-1]["score"]:
        name = get_name_input()
        add_score(level, name, score)

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
            draw_text(str(i + 1), x + 45, 165, medium_font)

        start_button_rect = pygame.Rect(300, 400, 300, 90)
        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        draw_text("▶ START", 340, 420, small_font, WHITE)

        highscore_button_rect = pygame.Rect(620, 400, 150, 90)
        pygame.draw.rect(screen, GRAY, highscore_button_rect, border_radius=12)
        draw_text("TOP 10", 640, 420, small_font, BLACK)

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
                elif highscore_button_rect.collidepoint(x, y):
                    show_highscores()

        pygame.display.update()
        clock.tick(30)

try:
    menu()
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
