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

# Paths for storing scores
RESULTS_FOLDER = "wyniki"
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

def results_file(level):
    return os.path.join(RESULTS_FOLDER, f"highscores_level_{level}.json")

def load_highscores(level):
    try:
        with open(results_file(level), "r") as f:
            return json.load(f)
    except:
        return []

def save_highscores(level, scores):
    with open(results_file(level), "w") as f:
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

        # STOP button
        stop_button_rect = pygame.Rect(800, 500, 200, 80)
        pygame.draw.rect(screen, RED, stop_button_rect)
        # Draw STOP text centered inside the button rect
        stop_text_surface = small_font.render("■ STOP", True, WHITE)
        stop_text_rect = stop_text_surface.get_rect(center=stop_button_rect.center)
        screen.blit(stop_text_surface, stop_text_rect)

        # Highscore button
        highscore_button_rect = pygame.Rect(50, 500, 200, 80)
        pygame.draw.rect(screen, BLUE, highscore_button_rect)
        highscore_text_surface = small_font.render("HIGHSCORE", True, WHITE)
        highscore_text_rect = highscore_text_surface.get_rect(center=highscore_button_rect.center)
        screen.blit(highscore_text_surface, highscore_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if stop_button_rect.collidepoint(event.pos):
                    stop_requested = True
                elif highscore_button_rect.collidepoint(event.pos):
                    show_highscores(level)

        pygame.display.update()
        clock.tick(60)

    for lp in led_pins:
        GPIO.output(lp, False)

    screen.fill(WHITE)
    draw_centered_text("KONIEC", 220, font)
    draw_centered_text(f"Twój wynik: {score}", 320, font)
    pygame.display.update()

    # Check if score qualifies for top 10
    scores = load_highscores(level)
    if len(scores) < 10 or score > scores[-1]["score"]:
        name = enter_name()
        add_score(level, name, score)

    time.sleep(2)

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

        start_button_rect = pygame.Rect(300, 400, 450, 90)
        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        draw_centered_text("▶ START", 445, small_font, WHITE)

        highscore_button_rect = pygame.Rect(770, 400, 230, 90)
        pygame.draw.rect(screen, BLUE, highscore_button_rect, border_radius=12)
        # Correct centered text for highscore button
        hs_text_surface = small_font.render("HIGHSCORE", True, WHITE)
        hs_text_rect = hs_text_surface.get_rect(center=highscore_button_rect.center)
        screen.blit(hs_text_surface, hs_text_rect)

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
                    show_highscores(level)

        pygame.display.update()
        clock.tick(30)

def show_highscores(level):
    scores = load_highscores(level)
    back_button_rect = pygame.Rect(950, 10, 60, 60)
    while True:
        screen.fill(WHITE)
        draw_centered_text(f"Top 10 wyniki - poziom {level}", 60, medium_font)

        y = 120
        for idx, entry in enumerate(scores):
            name = entry["name"]
            sc = entry["score"]
            text = f"{idx + 1}. {name} - {sc}"
            draw_text(text, 100, y, medium_font)
            y += 50

        pygame.draw.rect(screen, RED, back_button_rect)
        # Draw "X" for close button centered
        x_surface = medium_font.render("X", True, WHITE)
        x_rect = x_surface.get_rect(center=back_button_rect.center)
        screen.blit(x_surface, x_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(event.pos):
                    return

        pygame.display.update()
        clock.tick(30)

def enter_name():
    # Simple on-screen keyboard for name input
    name = ""
    keys = [
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        list("ZXCVBNM"),
        ["SPACE", "BACK"]
    ]

    button_width = 80
    button_height = 80
    keyboard_x = 100
    keyboard_y = 320 - 50  # <-- podniesione o 50 px względem poprzednio (370->320)

    def draw_keyboard():
        screen.fill(WHITE)
        draw_centered_text("Podaj swoje imię", 60, medium_font)
        # Display current name
        draw_text(name, 100, 120, font)

        y = keyboard_y
        for row in keys:
            x = keyboard_x
            for key in row:
                rect = pygame.Rect(x, y, button_width, button_height)
                pygame.draw.rect(screen, GRAY, rect, border_radius=10)
                # Draw key text centered inside button
                key_text_surface = small_font.render(key if key != "SPACE" else " ", True, BLACK)
                key_text_rect = key_text_surface.get_rect(center=rect.center)
                screen.blit(key_text_surface, key_text_rect)
                x += button_width + 10
            y += button_height + 10

        # Draw "Zapisz" and "Wróć" buttons below keyboard
        save_rect = pygame.Rect(700, keyboard_y + (button_height + 10) * len(keys) + 10, 150, 80)
        back_rect = pygame.Rect(900, keyboard_y + (button_height + 10) * len(keys) + 10, 120, 80)

        pygame.draw.rect(screen, BLUE, save_rect, border_radius=12)
        save_text_surf = medium_font.render("Zapisz", True, WHITE)
        save_text_rect = save_text_surf.get_rect(center=save_rect.center)
        screen.blit(save_text_surf, save_text_rect)

        pygame.draw.rect(screen, RED, back_rect, border_radius=12)
        back_text_surf = medium_font.render("Wróć", True, WHITE)
        back_text_rect = back_text_surf.get_rect(center=back_rect.center)
        screen.blit(back_text_surf, back_text_rect)

        return save_rect, back_rect, keys, button_width, button_height, keyboard_x, keyboard_y

    while True:
        save_rect, back_rect, keys, button_width, button_height, keyboard_x, keyboard_y = draw_keyboard()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                # Check keyboard keys
                y_pos = keyboard_y
                for row in keys:
                    x_pos = keyboard_x
                    for key in row:
                        key_rect = pygame.Rect(x_pos, y_pos, button_width, button_height)
                        if key_rect.collidepoint(x, y):
                            if key == "SPACE":
                                name += " "
                            elif key == "BACK":
                                name = name[:-1]
                            else:
                                name += key
                        x_pos += button_width + 10
                    y_pos += button_height + 10

                if save_rect.collidepoint(x, y):
                    if name.strip() == "":
                        # Ignore empty name, continue input
                        continue
                    return name.strip()
                if back_rect.collidepoint(x, y):
                    return "Anon"  # Return default anonymous name

        pygame.display.update()
        clock.tick(30)

try:
    menu()
finally:
    GPIO.cleanup()
    pygame.quit()
    sys.exit()
