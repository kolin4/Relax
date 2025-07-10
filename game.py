# Additional imports
import os
import json

# Constants for highscore
HIGHSCORE_DIR = "wyniki"
HIGHSCORE_FILE_TEMPLATE = os.path.join(HIGHSCORE_DIR, "level_{level}.json")
MAX_HIGHSCORES = 10

# Ensure highscore directory exists
if not os.path.exists(HIGHSCORE_DIR):
    os.makedirs(HIGHSCORE_DIR)

def load_highscores(level):
    path = HIGHSCORE_FILE_TEMPLATE.format(level=level)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return []

def save_highscores(level, scores):
    path = HIGHSCORE_FILE_TEMPLATE.format(level=level)
    with open(path, 'w') as f:
        json.dump(scores, f)

def maybe_add_highscore(level, score):
    scores = load_highscores(level)
    if len(scores) < MAX_HIGHSCORES or score > scores[-1]['score']:
        name = prompt_for_name()
        scores.append({"name": name, "score": score})
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores = scores[:MAX_HIGHSCORES]
        save_highscores(level, scores)

def prompt_for_name():
    name = ""
    running = True
    while running:
        screen.fill(WHITE)
        draw_centered_text("Wpisz swoje imie:", 200, medium_font)
        draw_centered_text(name, 300, digital_font)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Anonim"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(name) > 0:
                    running = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 10:
                    name += event.unicode
    return name

def show_highscores(level):
    scores = load_highscores(level)
    running = True
    while running:
        screen.fill(WHITE)
        draw_centered_text(f"Top 10 - Poziom {level}", 60, font)

        for idx, entry in enumerate(scores):
            draw_text(f"{idx+1}. {entry['name']} - {entry['score']}", 200, 130 + idx * 40, small_font)

        exit_button = pygame.Rect(940, 10, 60, 40)
        pygame.draw.rect(screen, RED, exit_button)
        draw_text("X", 955, 10, medium_font, WHITE)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if exit_button.collidepoint(event.pos):
                    running = False

# Add highscore button to menu()
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

        start_button_rect = pygame.Rect(300, 400, 200, 90)
        highscore_button_rect = pygame.Rect(550, 400, 200, 90)

        pygame.draw.rect(screen, BLUE, start_button_rect, border_radius=12)
        pygame.draw.rect(screen, GRAY, highscore_button_rect, border_radius=12)

        draw_centered_text("▶ START", 445, small_font, WHITE)
        draw_centered_text("Highscore", 445, small_font, BLACK)

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
                    maybe_add_highscore(level, score)
                if highscore_button_rect.collidepoint(x, y):
                    show_highscores(level)

        pygame.display.update()
        clock.tick(30)
