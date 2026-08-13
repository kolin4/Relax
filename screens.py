"""
screens.py
Poszczególne widoki gry, każdy jako mała, samodzielna klasa z metodami
handle_event(event) i draw(screen). Ekrany, które mają logikę zmienną
w czasie (rozgrywka), mają dodatkowo update().

Przełączanie widoków odbywa się przez atrybut `next_screen`, ustawiany
na krotkę (nazwa_ekranu, ...argumenty). Odczytuje go pętla główna w main.py.
"""
import random
import subprocess
import pygame

import config as cfg
import ui
import highscores as hs


class MenuScreen:
    def __init__(self, fonts, level):
        self.fonts = fonts
        self.level = level
        self.next_screen = None

        self.level_buttons = []
        card_w, card_h = 130, 90
        gap = 20
        total_w = cfg.NUM_LEVELS * card_w + (cfg.NUM_LEVELS - 1) * gap
        start_x = (cfg.SCREEN_WIDTH - total_w) // 2
        for i in range(cfg.NUM_LEVELS):
            rect = (start_x + i * (card_w + gap), 190, card_w, card_h)
            self.level_buttons.append(
                ui.Button(rect, str(i + 1), fonts.medium,
                          bg=cfg.GRAY_LIGHT, fg=cfg.TEXT_DARK, bg_active=cfg.ACCENT)
            )

        self.start_button = ui.Button((cfg.SCREEN_WIDTH // 2 - 260, 420, 240, 90),
                                       "START", fonts.title, bg=cfg.SUCCESS)
        self.highscore_button = ui.Button((cfg.SCREEN_WIDTH // 2 + 20, 420, 240, 90),
                                           "WYNIKI", fonts.title, bg=cfg.ACCENT)

        # pojedyncza ikona w lewym gornym rogu, rozwija dropdown z opcjami
        # zamkniecia gry / wylaczenia Raspberry Pi
        self.power_icon = ui.Button((20, 20, 56, 56), "...", fonts.medium,
                                     bg=cfg.GRAY, fg=cfg.WHITE)
        self.menu_open = False
        self.option_terminal = ui.Button((20, 84, 260, 56),
                                          "Wyjdz do terminala", fonts.small,
                                          bg=cfg.GRAY_LIGHT, fg=cfg.TEXT_DARK)
        self.option_shutdown = ui.Button((20, 146, 260, 56),
                                          "Wylacz Raspberry Pi", fonts.small,
                                          bg=cfg.DANGER, fg=cfg.WHITE)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        pos = event.pos

        if self.menu_open:
            # dropdown jest otwarty: albo klikamy jedna z opcji, albo
            # cokolwiek innego, co je po prostu zamyka (bez dalszej akcji)
            if self.option_terminal.is_clicked(pos):
                self.next_screen = ("quit",)
            elif self.option_shutdown.is_clicked(pos):
                subprocess.run(["sudo", "shutdown", "-h", "now"])
                self.next_screen = ("quit",)
            self.menu_open = False
            return

        if self.power_icon.is_clicked(pos):
            self.menu_open = True
            return

        for i, btn in enumerate(self.level_buttons):
            if btn.is_clicked(pos):
                self.level = i + 1
        if self.start_button.is_clicked(pos):
            self.next_screen = ("game", self.level)
        elif self.highscore_button.is_clicked(pos):
            self.next_screen = ("highscores", self.level)

    def draw(self, screen):
        screen.fill(cfg.BG)
        ui.draw_centered_text(screen, "Reaction Tester", 70, self.fonts.title, cfg.TEXT_DARK)
        ui.draw_centered_text(screen, "Wybierz poziom trudnosci", 130, self.fonts.small, cfg.TEXT_MUTED)

        for i, btn in enumerate(self.level_buttons):
            btn.draw(screen, active=(self.level == i + 1))

        timing_ms, simultaneous = cfg.LEVEL_TIMINGS[self.level]
        info = f"Czas reakcji: {timing_ms} ms"
        if simultaneous > 1:
            info += "  *  2 diody naraz"
        ui.draw_centered_text(screen, info, 320, self.fonts.small, cfg.TEXT_MUTED)

        self.start_button.draw(screen)
        self.highscore_button.draw(screen)

        self.power_icon.draw(screen)
        if self.menu_open:
            ui.draw_card(screen, (16, 80, 268, 126), color=cfg.WHITE, radius=12)
            self.option_terminal.draw(screen)
            self.option_shutdown.draw(screen)


class HighscoreScreen:
    def __init__(self, fonts, level):
        self.fonts = fonts
        self.level = level
        self.next_screen = None
        self.close_button = ui.Button((cfg.SCREEN_WIDTH - 80, 20, 56, 56), "X",
                                       fonts.small, bg=cfg.DANGER)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.close_button.is_clicked(event.pos):
            self.next_screen = ("menu", self.level)

    def draw(self, screen):
        screen.fill(cfg.BG)
        ui.draw_centered_text(screen, f"NAJLEPSZE WYNIKI - POZIOM {self.level}", 60,
                               self.fonts.title, cfg.TEXT_DARK)

        card = pygame.Rect(212, 130, 600, 420)
        ui.draw_card(screen, card)

        scores = hs.load_highscores(self.level)
        if not scores:
            ui.draw_centered_text(screen, "Brak wynikow - zagraj pierwszy!", 340,
                                   self.fonts.small, cfg.TEXT_MUTED)
        else:
            medal_colors = {0: (196, 154, 32), 1: (140, 145, 155), 2: (170, 110, 55)}
            for idx, entry in enumerate(scores):
                y = 165 + idx * 38
                color = medal_colors.get(idx, cfg.TEXT_DARK)
                ui.draw_text(screen, f"{idx + 1}.", 250, y, self.fonts.small, color)
                ui.draw_text(screen, entry["name"], 310, y, self.fonts.small, color)
                ui.draw_text(screen, str(entry["score"]), 720, y, self.fonts.small, color)

        self.close_button.draw(screen)


class NameEntryScreen:
    def __init__(self, fonts, level, score):
        self.fonts = fonts
        self.level = level
        self.score = score
        self.name = ""
        self.keyboard = ui.OnScreenKeyboard(fonts.medium)
        self.next_screen = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            result = self.keyboard.handle_click(event.pos)
            if result == "BACK":
                self.name = self.name[:-1]
            elif result == "OK":
                if self.name.strip():
                    hs.add_score(self.level, self.name.strip(), self.score)
                    self.next_screen = ("highscores", self.level)
            elif result and len(self.name) < cfg.MAX_NAME_LENGTH:
                self.name += result

    def draw(self, screen):
        screen.fill(cfg.BG)
        ui.draw_centered_text(screen, "Nowy rekord!", 90, self.fonts.title, cfg.SUCCESS)
        ui.draw_centered_text(screen, "Podaj swoje imie", 140, self.fonts.small, cfg.TEXT_MUTED)

        box = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 220, 170, 440, 70)
        ui.draw_card(screen, box, color=cfg.WHITE)
        ui.draw_centered_text(screen, self.name if self.name else "_", box.centery,
                               self.fonts.title, cfg.TEXT_DARK)

        self.keyboard.draw(screen)


class GameScreen:
    """Odliczanie -> rozgrywka na 8 pol -> ekran koncowy."""

    STATE_COUNTDOWN = "countdown"
    STATE_PLAYING = "playing"
    STATE_FINISHED = "finished"

    def __init__(self, fonts, level, controller):
        self.fonts = fonts
        self.level = level
        self.controller = controller
        self.next_screen = None

        self.state = self.STATE_COUNTDOWN
        self.countdown_start = pygame.time.get_ticks()
        self.countdown_value = 3

        self.score = 0
        self.combo = 0
        self.multiplier = 1.0
        self.active_pads = set()
        self.pad_started_at = {}
        self.next_light_time = None
        self.game_start_time = None
        self.correct_flash = {}   # index -> znacznik czasu (ms), do kiedy migać
        self.wrong_flash = {}
        self.finished_at = None
        self.prev_pressed = [False] * cfg.NUM_PADS  # do wykrywania pojedynczego kliknięcia

        self.stop_button = ui.Button((cfg.SCREEN_WIDTH - 220, cfg.SCREEN_HEIGHT - 100, 180, 70),
                                      "STOP", fonts.small, bg=cfg.DANGER)

    def _timing(self):
        return cfg.LEVEL_TIMINGS.get(self.level, (1000, 1))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == self.STATE_PLAYING and self.stop_button.is_clicked(event.pos):
                self._end_game()

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == self.STATE_COUNTDOWN:
            elapsed = now - self.countdown_start
            self.countdown_value = 3 - elapsed // 1000
            if self.countdown_value <= 0:
                self._start_playing(now)
            return

        if self.state == self.STATE_PLAYING:
            self._update_playing(now)
            return

        if self.state == self.STATE_FINISHED:
            if now - self.finished_at > 1500:
                if hs.qualifies(self.level, self.score):
                    self.next_screen = ("name_entry", self.level, self.score)
                else:
                    self.next_screen = ("menu", self.level)

    def _update_playing(self, now):
        elapsed = (now - self.game_start_time) / 1000
        if elapsed >= cfg.GAME_DURATION:
            self._end_game()
            return

        led_time, simultaneous = self._timing()

        # zapal nowe diody, jesli jest na to czas i miejsce
        if now >= self.next_light_time and len(self.active_pads) < simultaneous:
            available = [i for i in range(cfg.NUM_PADS) if i not in self.active_pads]
            if available:
                pad = random.choice(available)
                self.active_pads.add(pad)
                self.pad_started_at[pad] = now
                self.controller.set_led(pad, True)
            self.next_light_time = now + led_time // max(1, simultaneous)

        # dioda, ktora nikt nie trafil w czasie - gasnie, krotki czerwony
        # blysk sygnalizuje przegapienie, combo pada
        for pad in list(self.active_pads):
            if now - self.pad_started_at[pad] >= led_time:
                self.controller.set_led(pad, False)
                self.active_pads.discard(pad)
                self.combo = 0
                self.multiplier = 1.0
                self.wrong_flash[pad] = now + 150

        # sprawdz przyciski - liczy sie tylko moment wcisniecia (zbocze
        # narastajace), nie samo trzymanie, wiec przytrzymanie przycisku
        # nie naliczy punktow (dodatnich ani ujemnych) w kolko
        currently_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]
        for i in range(cfg.NUM_PADS):
            just_pressed = currently_pressed[i] and not self.prev_pressed[i]
            if not just_pressed:
                continue
            if i in self.active_pads:
                self.score += int(round(1 * self.multiplier))
                self.combo += 1
                self.multiplier = min(
                    cfg.MAX_COMBO_MULTIPLIER,
                    1.0 + (self.combo // cfg.COMBO_HITS_PER_STEP) * cfg.COMBO_STEP
                )
                self.controller.set_led(i, False)
                self.active_pads.discard(i)
                self.correct_flash[i] = now + 150
            else:
                self.score -= 1
                self.combo = 0
                self.multiplier = 1.0
                self.wrong_flash[i] = now + 150
        self.prev_pressed = currently_pressed

        self.correct_flash = {k: v for k, v in self.correct_flash.items() if v > now}
        self.wrong_flash = {k: v for k, v in self.wrong_flash.items() if v > now}

    def _start_playing(self, now):
        self.state = self.STATE_PLAYING
        self.game_start_time = now
        self.next_light_time = now
        self.score = 0
        self.combo = 0
        self.multiplier = 1.0
        # jesli ktos trzyma przycisk juz w momencie startu (np. od odliczania),
        # nie traktuj tego jako "swiezego" kliknieca w pierwszej klatce
        self.prev_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]

    def _end_game(self):
        self.controller.all_off()
        self.active_pads.clear()
        self.state = self.STATE_FINISHED
        self.finished_at = pygame.time.get_ticks()

    def draw(self, screen):
        screen.fill(cfg.BG)

        if self.state == self.STATE_COUNTDOWN:
            ui.draw_centered_text(screen, str(max(1, self.countdown_value)), 300, self.fonts.huge)
            return

        if self.state == self.STATE_FINISHED:
            ui.draw_centered_text(screen, "KONIEC GRY", 200, self.fonts.title, cfg.TEXT_DARK)
            ui.draw_centered_text(screen, f"Wynik: {self.score}", 300, self.fonts.huge, cfg.ACCENT)
            return

        # STATE_PLAYING
        elapsed = (pygame.time.get_ticks() - self.game_start_time) / 1000
        remaining = max(0.0, cfg.GAME_DURATION - elapsed)

        ui.draw_text(screen, f"Wynik: {self.score}", 40, 24, self.fonts.medium)
        ui.draw_centered_text(screen, f"{remaining:04.1f}s", 60, self.fonts.digital, cfg.TEXT_DARK)

        # poziom i combo w prawym gornym rogu, z dala od centralnego timera
        combo_color = cfg.SUCCESS if self.multiplier > 1 else cfg.TEXT_MUTED
        level_surf = self.fonts.medium.render(f"Poziom {self.level}", True, cfg.TEXT_MUTED)
        combo_surf = self.fonts.small.render(f"Combo x{self.multiplier:.1f}", True, combo_color)
        right_edge = cfg.SCREEN_WIDTH - 40
        screen.blit(level_surf, (right_edge - level_surf.get_width(), 24))
        screen.blit(combo_surf, (right_edge - combo_surf.get_width(), 62))

        pad_area = pygame.Rect(242, 108, 540, 380)
        ui.draw_pad_grid(screen, pad_area, self.active_pads,
                          self.correct_flash, self.wrong_flash, self.fonts.small)

        self.stop_button.draw(screen)
