import pygame
import RPi.GPIO as GPIO
import time
import random
import sys
import os
import json

# === HIGH SCORE SETUP ===
SCORES_DIR = "wyniki"
os.makedirs(SCORES_DIR, exist_ok=True)

# === GPIO setup ===
button_pins = [5, 6]  # Two buttons
led_pins = [17, 27]   # Two LEDs
GPIO.setmode(GPIO.BCM)
for bp in button_pins:
    GPIO.setup(bp, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for lp in led_pins:
    GPIO.setup(lp, GPIO.OUT)
    GPIO.output(lp, False)

# === Pygame setup ===
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

# === Colors ===
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
RED = (200, 0, 0)
BLACK = (0, 0, 0)

# === Game state ===
level = 1
score = 0
game_duration = 60
stop_requested = False
showing_highscores = False
entering_name = False
name_input = ""

# === Timing per level ===
LEVEL_TIMINGS = {
    1: 1000,
    2: 900,
    3: 800,
    4: 500,
    5: 300
}

# === Highscore functions ===
def get_highscore_file():
    return os.path.join(SCORES_DIR, f"level{level}_scores.json")

def load_highscores():
    try:
        with open(get_highscore_file(), "r") as f:
            return json.load(f)
    except:
        return []

def save_highscores(scores):
    with open(get_highscore_file(), "w") as f:
        json.dump(scores, f)

def add_score(name, score):
    scores = load_highscores()
    scores.append({"name": name, "score": score})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]
    save_highscores(scores)

# === UI Drawing ===
def draw_text(text, x, y, font, color=BLACK):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def draw_centered_text(text, y, font, color=BLACK):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(512, y))
    screen.blit(surface, rect)

# === Keyboard Drawing ===
def draw_keyboard():
    keys = [
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM"),
    ]
    key_width = 80
    key_height = 80
    spacing = 10
    start_y = 300
    key_rects = []

    for row_index, row in enumerate(keys):
        total_width = len(row) * (key_width + spacing) - spacing
        start_x = (1024 - total_width) // 2
        for col_index, letter in enumerate(row):
            x = start_x + col_index * (key_width + spacing)
            y = start_y + row_index * (key_height + spacing)
            rect = pygame.Rect(x, y, key_width, key_height)
            pygame.draw.rect(screen, GRAY, rect, border_radius=8)
            letter_surface = medium_font.render(letter, True, BLACK)
            letter_rect = letter_surface.get_rect(center=rect.center)
            screen.blit(letter_surface, letter_rect)
            key_rects.append((rect, letter))

    # BACKSPACE and OK buttons
    back_rect = pygame.Rect(300, 540, 180, 50)
    ok_rect = pygame.Rect(550, 540, 180, 50)
    pygame.draw.rect(screen, RED, back_rect, border_radius=8)
    pygame.draw.rect(screen, GREEN, ok_rect, border_radius=8)
    screen.blit(small_font.render("← BACK", True, WHITE), (back_rect.x + 20, back_rect.y + 10))
    screen.blit(small_font.render("OK", True, WHITE), (ok_rect.x + 60, ok_rect.y + 10))
    return key_rects, back_rect, ok_rect

# === Countdown ===
def countdown():
    for i in range(3, 0, -1):
        screen.fill(WHITE)
        draw_centered_text(str(i), 300, font)
        pygame.display.update()
        time.sleep(1)

# === Game Loop ===
def game_loop():
    global score, stop_requested, level, entering_name, name_input
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
        pygame.draw.rect(screen, RED, stop_button_rect, border_radius=8)
        stop_text = small_font.render("■ STOP", True, WHITE)
        screen.blit(stop_text, stop_button_rect.move((stop_button_rect.width - stop_text.get_width()) // 2, (stop_button_rect.height - stop_text.get_height()) // 2))

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

    scores = load_highscores()
    if len(scores) < 10 or score > scores[-1]["score"]:
        entering_name = True
        name_input = ""
        while entering_name:
            screen.fill(WHITE)
            draw_centered_text("Nowy rekord! Podaj imię:", 100, medium_font)
            draw_centered_text(name_input, 180, font)
            key_rects, back_rect, ok_rect = draw_keyboard()
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    entering_name = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if back_rect.collidepoint(pos):
                        name_input = name_input[:-1]
                    elif ok_rect.collidepoint(pos):
                        if name_input:
                            add_score(name_input, score)
                            entering_name = False
                    else:
                        for rect, char in key_rects:
                            if rect.collidepoint(pos):
                                if len(name_input) < 10:
                                    name_input += char

# === Highscore display ===
def show_highscores():
    global showing_highscores
    showing_highscores = True
    while showing_highscores:
        screen.fill(WHITE)
        draw_centered_text(f"TOP 10 - LEVEL {level}", 50, medium_font)
        scores = load_highscores()
        for idx, entry in enumerate(scores):
            draw_text(f"{idx + 1}. {entry['name']} - {entry['score']}", 200, 120 + idx * 40, small_font)

        close_rect = pygame.Rect(960, 20, 40, 40)
        pygame.draw.rect(screen, RED, close_rect, border_radius=8)
        screen.blit(small_font.render("X", True, WHITE), (close_rect.x + 8, close_rect.y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showing_highscores = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if close_rect.collidepoint(event.pos):
                    showing_highscores = False

        pygame.display.update()
        clock.tick(30)

# === Main Menu ===
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
        highscore_button_rect = pygame.Rect(620, 400, 180, 90)

        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        pygame.draw.rect(screen, GRAY, highscore_button_rect, border_radius=12)

        start_text = small_font.render("▶ START", True, WHITE)
        screen.blit(start_text, start_button_rect.move((start_button_rect.width - start_text.get_width()) // 2, (start_button_rect.height - start_text.get_height()) // 2))

        hs_text = small_font.render("Highscore", True, BLACK)
        screen.blit(hs_text, highscore_button_rect.move((highscore_button_rect.width - hs_text.get_width()) // 2, (highscore_button_rect.height - hs_text.get_height()) // 2))

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
