"""
main.py
Punkt wejscia gry. Inicjalizuje pygame i GPIO, po czym uruchamia petle
glowna, ktora rysuje aktualny ekran i przelacza sie miedzy nimi na
podstawie atrybutu `next_screen`.

Uruchomienie: python3 main.py
"""
import sys
import pygame

import config as cfg
from fonts import Fonts
from gpio_io import ButtonLedController
import screens


def make_screen(name, fonts, controller, level, score=None):
    if name == "menu":
        return screens.MenuScreen(fonts, level)
    if name == "highscores":
        return screens.HighscoreScreen(fonts, level)
    if name == "game":
        return screens.GameScreen(fonts, level, controller)
    if name == "name_entry":
        return screens.NameEntryScreen(fonts, level, score)
    raise ValueError(f"Nieznany ekran: {name}")


def main():
    pygame.init()
    screen_surface = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
    pygame.display.set_caption("Reaction Tester")
    clock = pygame.time.Clock()
    fonts = Fonts()

    controller = ButtonLedController(cfg.BUTTON_PINS, cfg.LED_PINS)

    current = screens.MenuScreen(fonts, level=1)

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                # ESC jako awaryjne wyjscie z gry, niezaleznie od aktualnego ekranu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                current.handle_event(event)

            if hasattr(current, "update"):
                current.update()

            current.draw(screen_surface)
            pygame.display.update()
            clock.tick(cfg.FPS)

            if current.next_screen is not None:
                name, *rest = current.next_screen
                if name == "quit":
                    return
                level = rest[0] if rest else 1
                score = rest[1] if len(rest) > 1 else None
                current = make_screen(name, fonts, controller, level, score)
    finally:
        controller.cleanup()
        pygame.quit()


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit()
