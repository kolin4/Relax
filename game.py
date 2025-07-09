import pygame
import RPi.GPIO as GPIO
import time
import sys
import random

# GPIO setup
button_pins = [5, 6]       # dwa przyciski
led_pins = [17, 27]        # dwie diody LED
GPIO.setmode(GPIO.BCM)
for bp in button_pins:
    GPIO.setup(bp, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for lp in led_pins:
    GPIO.setup(lp, GPIO.OUT)
    GPIO.output(lp, False)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((1024, 600))
pygame.display.set_caption("Reaction Tester 2BTN")
font = pygame.font.SysFont("Arial", 60)
medium_font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 40)
digital_font = pygame.font.SysFont("Courier", 110)
clock = pygame.time.Clock()

# Kolory
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (200,0,0)
GREEN = (0,200,0)
GRAY = (180,180,180)
BLUE = (0,100,255)

# Parametry gry
level = 1
score = 0
game_duration = 60  # sekund
stop_requested = False

# Konfiguracja LED dla poziomów
LEVEL_SETTINGS = {
    1: (1000, (1200, 2500)),
    2: (800, (1000, 2000)),
    3: (600, (800, 1800)),
    4: (500, (700, 1500)),
    5: (400, (600, 1300)),
}

def draw_text(text, x, y, font, color=BLACK):
    surf = font.render(text, True, color)
    screen.blit(surf, (x,y))

def draw_centered_text(text, y, font, color=BLACK):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(512,y))
    screen.blit(surf, rect)

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

    led_time, led_interval = LEVEL_SETTINGS[level]
    start = pygame.time.get_ticks()
    led_on = False
    led_start = 0
    next_led = start + random.randint(*led_interval)

    while not stop_requested:
        now = pygame.time.get_ticks()
        elapsed = (now - start) / 1000
        if elapsed >= game_duration:
            break

        screen.fill(WHITE)
        # Timer i wynik
        timer_text = f"{game_duration - elapsed:05.2f}s"
        t_surf = digital_font.render(timer_text, True, RED)
        t_rect = t_surf.get_rect(center=(512,70))
        screen.blit(t_surf, t_rect)
        draw_text(f"Score: {score}", 50, 30, medium_font)
        draw_text(f"Level: {level}", 800, 30, small_font)

        # Obsługa LED
        if not led_on and now >= next_led:
            current = random.randint(0,1)
            GPIO.output(led_pins[current], True)
            led_on = True
            led_start = now
            active = current

        if led_on and now - led_start > led_time:
            GPIO.output(led_pins[active], False)
            led_on = False
            next_led = now + random.randint(*led_interval)

        # Sprawdzenie przycisku
        if led_on:
            if GPIO.input(button_pins[active]) == GPIO.LOW:
                score += 1
                GPIO.output(led_pins[active], False)
                led_on = False
                next_led = now + random.randint(*led_interval)
                time.sleep(0.2)

        # Stop button
        stop_rect = pygame.Rect(800,500,200,80)
        pygame.draw.rect(screen, RED, stop_rect, border_radius=8)
        draw_centered_text("■ STOP", 540, small_font, WHITE)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                stop_requested = True
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if stop_rect.collidepoint(e.pos):
                    stop_requested = True

        pygame.display.update()
        clock.tick(60)

    # Koniec gry
    for lp in led_pins:
        GPIO.output(lp, False)
    screen.fill(WHITE)
    draw_centered_text("KONIEC", 220, font)
    draw_centered_text(f"Twój wynik: {score}", 320, font)
    pygame.display.update()
    time.sleep(5)

def menu():
    global level
    while True:
        screen.fill(WHITE)
        draw_centered_text("Wybierz poziom:", 80, medium_font)

        for i in range(5):
            x = 100 + i * 170
            rect = pygame.Rect(x,150,120,80)
            col = GREEN if level==i+1 else GRAY
            pygame.draw.rect(screen, col, rect, border_radius=12)
            num_surf = small_font.render(str(i+1), True, BLACK)
            num_rect = num_surf.get_rect(center=rect.center)
            screen.blit(num_surf, num_rect)

        start_rect = pygame.Rect(380,400,250,90)
        pygame.draw.rect(screen, BLUE, start_rect, border_radius=12)
        draw_centered_text("▶ START", 445, small_font, WHITE)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx,my = e.pos
                for i in range(5):
                    if pygame.Rect(100 + i * 170,150,120,80).collidepoint(mx,my):
                        level = i+1
                if start_rect.collidepoint(mx,my):
                    game_loop()

        pygame.display.update()
        clock.tick(30)

if __name__ == "__main__":
    try:
        menu()
    finally:
        GPIO.cleanup()
        pygame.quit()
        sys.exit()
