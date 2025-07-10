import pygame
import RPi.GPIO as GPIO
import time
import random
import sys
import os
import json

# === FOLDERS ===
SAVE_DIR = "wyniki"
os.makedirs(SAVE_DIR, exist_ok=True)

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

# === Level timings (ms) ===
LEVEL_TIMINGS = {
    1: 1000,
    2: 900,
    3: 800,
    4: 500,
    5: 300
}

# === Functions ===
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

def save_score(level, name, score):
    filename = os.path.join(SAVE_DIR, f"level_{level}.json")
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except:
        data = []
    data.append({"name": name, "score": score})
    data = sorted(data, key=lambda x: x["score"], reverse=True)[:10]
    with open(filename, "w") as f:
        json.dump(data, f)

def load_scores(level):
    filename = os.path.join(SAVE_DIR, f"level_{level}.json")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def show_keyboard():
    name = ""
    keys = [
        list("ABCDEF"),
        list("GHIJKL"),
        list("MNOPQR"),
        list("STUVWX"),
        list("YZ <- OK")
    ]
    key_size = 100
    key_margin = 10
    while True:
        screen.fill(WHITE)
        draw_centered_text("Podaj imię:", 80, medium_font)
        draw_centered_text(name, 150, font)

        for row_idx, row in enumerate(keys):
            for col_idx, char in enumerate(row):
                x = 50 + col_idx * (key_size + key_margin)
                y = 220 + row_idx * (key_size + key_margin)
                rect = pygame.Rect(x, y, key_size, key_size)
                pygame.draw.rect(screen, GRAY, rect)
                text_surf = small_font.render(char, True, BLACK)
                text_rect = text_surf.get_rect(center=rect.center)
                screen.blit(text_surf, text_rect)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ""
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for row_idx, row in enumerate(keys):
                    for col_idx, char in enumerate(row):
                        x = 50 + col_idx * (key_size + key_margin)
                        y = 220 + row_idx * (key_size + key_margin)
                        rect = pygame.Rect(x, y, key_size, key_size)
                        if rect.collidepoint(mx, my):
                            if char == "<-":
                                name = name[:-1]
                            elif char == "OK":
                                return name.strip()[:10]
                            else:
                                name += char


def show_highscores():
    showing = True
    while showing:
        scores = load_scores(level)
        screen.fill(WHITE)
        draw_centered_text(f"TOP 10 - Poziom {level}", 60, medium_font)
        for idx, entry in enumerate(scores):
            draw_text(f"{idx+1}. {entry['name']} - {entry['score']}", 300, 130 + idx * 40, small_font)
        close_btn = pygame.Rect(950, 10, 50, 50)
        pygame.draw.rect(screen, RED, close_btn)
        x_text = small_font.render("X", True, WHITE)
        x_rect = x_text.get_rect(center=close_btn.center)
        screen.blit(x_text, x_rect)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if close_btn.collidepoint(event.pos):
                    showing = False


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
        draw_text("■ STOP", 820, 520, small_font, WHITE)

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

    scores = load_scores(level)
    if len(scores) < 10 or score > scores[-1]['score']:
        name = show_keyboard()
        if name:
            save_score(level, name, score)

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
        draw_text("▶ START", 330, 420, small_font, WHITE)

        highscore_button_rect = pygame.Rect(620, 400, 200, 90)
        pygame.draw.rect(screen, GRAY, highscore_button_rect, border_radius=12)
        draw_text("Highscore", 635, 420, small_font)

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
