"""
main.py
Punkt wejscia gry. Inicjalizuje pygame i GPIO, po czym uruchamia petle
glowna, ktora rysuje aktualny ekran i przelacza sie miedzy nimi na
podstawie atrybutu `next_screen`.

Uruchomienie: python3 main.py
"""
import sys
import subprocess
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
    if name == "memory":
        return screens.MemoryScreen(fonts, controller)
    if name == "duel":
        return screens.DuelScreen(fonts, controller)
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
    splash_dismissed = False

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                # ESC jako awaryjne wyjscie z gry, niezaleznie od aktualnego ekranu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

                # Na konsoli (bez X) ekran dotykowy wysyla natywne zdarzenia
                # FINGERDOWN (wspolrzedne znormalizowane 0.0-1.0) zamiast
                # zdarzen myszy - tlumaczymy je tutaj na MOUSEBUTTONDOWN,
                # zeby caly istniejacy kod (przyciski, klawiatura ekranowa,
                # dropdown) dzialal bez zmian, niezaleznie od trybu.
                if event.type == pygame.FINGERDOWN:
                    x = int(event.x * cfg.SCREEN_WIDTH)
                    y = int(event.y * cfg.SCREEN_HEIGHT)
                    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1)

                current.handle_event(event)

            if hasattr(current, "update"):
                current.update()

            current.draw(screen_surface)
            pygame.display.update()

            # Dokladnie w momencie, gdy pierwsza klatka menu jest juz
            # narysowana na ekranie, zamykamy splash Plymouth (jesli byl
            # skonfigurowany, zeby czekac na to zamiast znikac sam po
            # zakonczeniu bootowania systemu). Dzieki temu przejscie ze
            # splasha do gry jest plynne, bez czarnego ekranu, niezaleznie
            # od tego jak dlugo trwal caly proces startu Pi. Bezpieczne
            # do wywolania takze wtedy, gdy plymouth juz nie dziala.
            if not splash_dismissed:
                subprocess.Popen(["sudo", "plymouth", "quit"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                splash_dismissed = True

            clock.tick(cfg.FPS)

            if current.next_screen is not None:
                name, *rest = current.next_screen
                if name == "quit":
                    return
                if name == "menu":
                    # przejscie do menu moze niesc ze soba tryb (reaction/memory/duel),
                    # zeby po powrocie z gry menu pokazalo sie w tym samym trybie
                    level = rest[0] if rest else 1
                    mode = rest[1] if len(rest) > 1 else "reaction"
                    current = screens.MenuScreen(fonts, level, mode=mode)
                else:
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
