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
    MODES = ["reaction", "memory", "duel"]
    MODE_LABELS = {"reaction": "Reaction Tester", "memory": "Pamiec", "duel": "Pojedynek"}

    def __init__(self, fonts, level, mode="reaction"):
        self.fonts = fonts
        self.level = level
        self.mode = mode  # "reaction" / "memory" / "duel"
        self.next_screen = None

        self.level_buttons = []
        card_w, card_h = 130, 90
        gap = 20
        total_w = cfg.NUM_LEVELS * card_w + (cfg.NUM_LEVELS - 1) * gap
        start_x = (cfg.SCREEN_WIDTH - total_w) // 2
        for i in range(cfg.NUM_LEVELS):
            rect = (start_x + i * (card_w + gap), 200, card_w, card_h)
            self.level_buttons.append(
                ui.Button(rect, str(i + 1), fonts.medium,
                          bg=cfg.GRAY_LIGHT, fg=cfg.TEXT_DARK, bg_active=cfg.ACCENT)
            )

        self.start_button = ui.Button((cfg.SCREEN_WIDTH // 2 - 260, 420, 240, 90),
                                       "START", fonts.title, bg=cfg.SUCCESS)
        self.highscore_button = ui.Button((cfg.SCREEN_WIDTH // 2 + 20, 420, 240, 90),
                                           "WYNIKI", fonts.title, bg=cfg.ACCENT)
        self.start_button_wide = ui.Button((cfg.SCREEN_WIDTH // 2 - 150, 420, 300, 90),
                                            "START", fonts.title, bg=cfg.SUCCESS)

        # przelacznik trybu gry: strzalki < > wokol nazwy trybu
        self.mode_left_arrow = ui.Button((296, 44, 56, 56), "<",
                                          fonts.medium, bg=cfg.GRAY_LIGHT, fg=cfg.TEXT_DARK)
        self.mode_right_arrow = ui.Button((672, 44, 56, 56), ">",
                                           fonts.medium, bg=cfg.GRAY_LIGHT, fg=cfg.TEXT_DARK)

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

    def _toggle_mode(self, direction):
        idx = self.MODES.index(self.mode)
        idx = (idx + direction) % len(self.MODES)
        self.mode = self.MODES[idx]

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

        if self.mode_left_arrow.is_clicked(pos):
            self._toggle_mode(-1)
            return
        if self.mode_right_arrow.is_clicked(pos):
            self._toggle_mode(1)
            return

        if self.mode == "reaction":
            for i, btn in enumerate(self.level_buttons):
                if btn.is_clicked(pos):
                    self.level = i + 1
            if self.start_button.is_clicked(pos):
                self.next_screen = ("game", self.level)
            elif self.highscore_button.is_clicked(pos):
                self.next_screen = ("highscores", self.level)
        elif self.mode == "memory":
            if self.start_button.is_clicked(pos):
                self.next_screen = ("memory",)
            elif self.highscore_button.is_clicked(pos):
                self.next_screen = ("highscores", "memory")
        else:  # duel - mecz na biezaco, bez tabeli wynikow
            if self.start_button_wide.is_clicked(pos):
                self.next_screen = ("duel",)

    def draw(self, screen):
        screen.fill(cfg.BG)

        self.mode_left_arrow.draw(screen)
        self.mode_right_arrow.draw(screen)
        ui.draw_centered_text(screen, self.MODE_LABELS[self.mode], 72, self.fonts.medium, cfg.TEXT_DARK)

        if self.mode == "reaction":
            ui.draw_centered_text(screen, "Wybierz poziom trudnosci", 160, self.fonts.small, cfg.TEXT_MUTED)
            for i, btn in enumerate(self.level_buttons):
                btn.draw(screen, active=(self.level == i + 1))

            timing_ms, simultaneous = cfg.LEVEL_TIMINGS[self.level]
            info = f"Czas reakcji: {timing_ms} ms"
            if simultaneous > 1:
                info += "  *  2 diody naraz"
            ui.draw_centered_text(screen, info, 320, self.fonts.small, cfg.TEXT_MUTED)
        elif self.mode == "memory":
            ui.draw_centered_text(screen, "Zapamietaj i powtorz sekwencje przyciskow", 200,
                                   self.fonts.small, cfg.TEXT_MUTED)
            ui.draw_centered_text(screen,
                                   f"Start: {cfg.MEMORY_START_LENGTH} krokow  *  "
                                   f"3 zycia  *  przyspieszenie po {cfg.MEMORY_MAX_LENGTH} krokach",
                                   240, self.fonts.small, cfg.TEXT_MUTED)
        else:  # duel
            ui.draw_centered_text(screen, "2 graczy: lewa polowa vs prawa polowa przyciskow", 200,
                                   self.fonts.small, cfg.TEXT_MUTED)
            ui.draw_centered_text(screen,
                                   f"Zapala sie sygnal - kto pierwszy klinie, ma punkt. "
                                   f"Falszywy start = punkt dla przeciwnika. Gra do {cfg.DUEL_WIN_SCORE} pkt.",
                                   240, self.fonts.small, cfg.TEXT_MUTED)
        if self.mode == "duel":
            self.start_button_wide.draw(screen)
        else:
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
            # z tabeli wynikow trybu Pamiec wracamy do menu w trybie domyslnym (reaction)
            back_level = 1 if self.level == "memory" else self.level
            self.next_screen = ("menu", back_level)

    def draw(self, screen):
        screen.fill(cfg.BG)
        title = "NAJLEPSZE WYNIKI - PAMIEC" if self.level == "memory" else f"NAJLEPSZE WYNIKI - POZIOM {self.level}"
        ui.draw_centered_text(screen, title, 60, self.fonts.title, cfg.TEXT_DARK)

        card = pygame.Rect(212, 130, 600, 420)
        ui.draw_card(screen, card)

        scores = hs.load_highscores(self.level)
        if not scores:
            ui.draw_centered_text(screen, "Brak wynikow - zagraj pierwszy!", 340,
                                   self.fonts.small, cfg.TEXT_MUTED)
        else:
            # sortujemy defensywnie (na wypadek recznej edycji pliku) i liczymy
            # pozycje tak, zeby remisy dzielily to samo miejsce w rankingu
            scores = sorted(scores, key=lambda e: e["score"], reverse=True)
            medal_colors = {0: (196, 154, 32), 1: (140, 145, 155), 2: (170, 110, 55)}
            last_score = None
            rank = 0
            for idx, entry in enumerate(scores):
                if entry["score"] != last_score:
                    rank = idx + 1
                    last_score = entry["score"]
                y = 165 + idx * 38
                color = medal_colors.get(rank - 1, cfg.TEXT_DARK)
                ui.draw_text(screen, f"{rank}.", 250, y, self.fonts.small, color)
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
        self.center_flash_color = None   # duzy kwadrat na srodku - kolor
        self.center_flash_until = 0      # do kiedy go pokazywac (ms)
        self.finished_at = None
        self.prev_pressed = [False] * cfg.NUM_PADS  # do wykrywania pojedynczego kliknięcia

        self.stop_button = ui.Button((cfg.SCREEN_WIDTH - 220, cfg.SCREEN_HEIGHT - 100, 180, 70),
                                      "STOP", fonts.small, bg=cfg.DANGER)

        # animacja testu LED podczas odliczania: piętra od góry do dołu,
        # zgodnie z fizycznym ukladem 2 gora / 2 gorne-boki / 2 dolne-boki / 2 dol
        self.LED_TEST_TIERS = [
            [0, 1],  # 1, 2 - gora
            [2, 7],  # 3, 8 - gorne boki
            [3, 6],  # 4, 7 - dolne boki
            [4, 5],  # 5, 6 - dol
        ]
        self.led_test_tier_index = -1
        self.led_test_active_pads = set()

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
            tier_count = len(self.LED_TEST_TIERS)
            tier_duration = cfg.COUNTDOWN_TIER_MS
            total_duration = tier_duration * tier_count

            # jedno zrodlo prawdy: i wyswietlana cyfra, i aktualne pietro LED
            # licza sie z tej samej zmiennej tier_index, wiec zmieniaja sie
            # zawsze w tej samej klatce (4 pietra -> odliczanie 4,3,2,1)
            tier_index = min(tier_count - 1, elapsed // tier_duration)
            self.countdown_value = tier_count - tier_index

            if tier_index != self.led_test_tier_index:
                # gasimy poprzednie piętro, zapalamy nowe
                for pad in self.led_test_active_pads:
                    self.controller.set_led(pad, False)
                self.led_test_tier_index = tier_index
                self.led_test_active_pads = set(self.LED_TEST_TIERS[tier_index])
                for pad in self.led_test_active_pads:
                    self.controller.set_led(pad, True)

            if elapsed >= total_duration:
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
                self.center_flash_color = cfg.DANGER
                self.center_flash_until = now + 150

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
                self.center_flash_color = cfg.SUCCESS
                self.center_flash_until = now + 150
            else:
                self.score -= 1
                self.combo = 0
                self.multiplier = 1.0
                self.wrong_flash[i] = now + 150
                self.center_flash_color = cfg.DANGER
                self.center_flash_until = now + 150
        self.prev_pressed = currently_pressed

        self.correct_flash = {k: v for k, v in self.correct_flash.items() if v > now}
        self.wrong_flash = {k: v for k, v in self.wrong_flash.items() if v > now}

    def _start_playing(self, now):
        self.controller.all_off()  # gasimy diody z animacji testowej odliczania
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
            pad_area = pygame.Rect(242, 108, 540, 380)
            ui.draw_pad_grid(screen, pad_area, self.led_test_active_pads,
                              {}, {}, self.fonts.small)
            ui.draw_centered_text(screen, str(max(1, self.countdown_value)),
                                   cfg.SCREEN_HEIGHT // 2, self.fonts.huge)
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

        # duzy kwadrat na srodku (tam gdzie fizycznie jest wyswietlacz) -
        # sygnalizuje trafienie (zielony) / pudlo lub przegapienie (czerwony)
        if self.center_flash_color is not None and pygame.time.get_ticks() < self.center_flash_until:
            size = 140
            center_rect = pygame.Rect(0, 0, size, size)
            center_rect.center = pad_area.center
            pygame.draw.rect(screen, self.center_flash_color, center_rect, border_radius=16)

        self.stop_button.draw(screen)


class MemoryScreen:
    """Tryb 'Pamiec' (Simon Says): gra pokazuje sekwencje przyciskow,
    user musi ja odtworzyc. Sekwencja rosnie co udana runde do
    MEMORY_MAX_LENGTH (faza 1), potem tempo pokazywania przyspiesza co
    runde (faza 2). 3 pomylki (zycia) konczą gre."""

    STATE_COUNTDOWN = "countdown"
    STATE_SHOWING = "showing"
    STATE_INPUT = "input"
    STATE_PAUSE = "pause"       # przerwa miedzy runda a nastepnym pokazem
    STATE_FINISHED = "finished"

    def __init__(self, fonts, controller):
        self.fonts = fonts
        self.controller = controller
        self.next_screen = None

        self.state = self.STATE_COUNTDOWN
        self.countdown_start = pygame.time.get_ticks()
        self.countdown_value = 4

        # animacja testu LED przy starcie - identyczna jak w GameScreen
        self.LED_TEST_TIERS = [[0, 1], [2, 7], [3, 6], [4, 5]]
        self.led_test_tier_index = -1
        self.led_test_active_pads = set()

        self.sequence = []
        self.step_ms = cfg.MEMORY_FLASH_ON_MS
        self.lives = cfg.MEMORY_LIVES
        self.score = 0

        self.show_index = 0
        self.show_step_state = "on"
        self.show_step_started_at = 0

        self.input_index = 0
        self.prev_pressed = [False] * cfg.NUM_PADS

        self.correct_flash = {}
        self.wrong_flash = {}
        self.center_flash_color = None
        self.center_flash_until = 0

        self.pause_started_at = 0
        self.pause_next_action = None  # "show_next_round" albo "retry_same"
        self.life_lost_this_pause = False

        self.finished_at = None

        self.stop_button = ui.Button((cfg.SCREEN_WIDTH - 220, cfg.SCREEN_HEIGHT - 100, 180, 70),
                                      "STOP", fonts.small, bg=cfg.DANGER)
        self.pad_area = pygame.Rect(242, 108, 540, 380)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.stop_button.is_clicked(event.pos):
                self._end_game()

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == self.STATE_COUNTDOWN:
            self._update_countdown(now)
            return
        if self.state == self.STATE_SHOWING:
            self._update_showing(now)
            return
        if self.state == self.STATE_INPUT:
            self._update_input(now)
            return
        if self.state == self.STATE_PAUSE:
            self._update_pause(now)
            return
        if self.state == self.STATE_FINISHED:
            if now - self.finished_at > 1500:
                if hs.qualifies("memory", self.score):
                    self.next_screen = ("name_entry", "memory", self.score)
                else:
                    self.next_screen = ("menu", 1)
            return

    # --- odliczanie z testem LED (identyczne jak w GameScreen) ---
    def _update_countdown(self, now):
        elapsed = now - self.countdown_start
        tier_count = len(self.LED_TEST_TIERS)
        tier_duration = cfg.COUNTDOWN_TIER_MS
        total_duration = tier_duration * tier_count

        tier_index = min(tier_count - 1, elapsed // tier_duration)
        self.countdown_value = tier_count - tier_index

        if tier_index != self.led_test_tier_index:
            for pad in self.led_test_active_pads:
                self.controller.set_led(pad, False)
            self.led_test_tier_index = tier_index
            self.led_test_active_pads = set(self.LED_TEST_TIERS[tier_index])
            for pad in self.led_test_active_pads:
                self.controller.set_led(pad, True)

        if elapsed >= total_duration:
            self.controller.all_off()
            self.sequence = [random.randrange(cfg.NUM_PADS) for _ in range(cfg.MEMORY_START_LENGTH)]
            self._begin_showing(now)

    # --- pokaz sekwencji ---
    def _begin_showing(self, now):
        self.state = self.STATE_SHOWING
        self.show_index = 0
        self.show_step_state = "on"
        self.show_step_started_at = now
        self.controller.set_led(self.sequence[0], True)

    def _update_showing(self, now):
        pad = self.sequence[self.show_index]
        if self.show_step_state == "on":
            if now - self.show_step_started_at >= self.step_ms:
                self.controller.set_led(pad, False)
                self.show_step_state = "off"
                self.show_step_started_at = now
        else:
            if now - self.show_step_started_at >= cfg.MEMORY_FLASH_GAP_MS:
                self.show_index += 1
                if self.show_index >= len(self.sequence):
                    self.state = self.STATE_INPUT
                    self.input_index = 0
                    self.prev_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]
                else:
                    next_pad = self.sequence[self.show_index]
                    self.controller.set_led(next_pad, True)
                    self.show_step_state = "on"
                    self.show_step_started_at = now

    def _active_show_pads(self):
        if self.state == self.STATE_SHOWING and self.show_step_state == "on":
            return {self.sequence[self.show_index]}
        return set()

    # --- wprowadzanie przez usera ---
    def _update_input(self, now):
        currently_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]
        for i in range(cfg.NUM_PADS):
            just_pressed = currently_pressed[i] and not self.prev_pressed[i]
            if not just_pressed:
                continue
            expected = self.sequence[self.input_index]
            if i == expected:
                self.correct_flash[i] = now + 150
                self.center_flash_color = cfg.SUCCESS
                self.center_flash_until = now + 150
                self.input_index += 1
                if self.input_index >= len(self.sequence):
                    self._on_round_complete(now)
            else:
                self.wrong_flash[i] = now + 150
                self.center_flash_color = cfg.DANGER
                self.center_flash_until = now + 150
                self._on_wrong_press(now)
            break  # jeden klik na klatke wystarczy do obslugi
        self.prev_pressed = currently_pressed

        self.correct_flash = {k: v for k, v in self.correct_flash.items() if v > now}
        self.wrong_flash = {k: v for k, v in self.wrong_flash.items() if v > now}

    def _on_round_complete(self, now):
        self.score += 1
        if len(self.sequence) < cfg.MEMORY_MAX_LENGTH:
            # sekwencja rosnie o jeden krok w ramach biezacego tempa
            self.sequence.append(random.randrange(cfg.NUM_PADS))
            self.pause_next_action = "show_next_round"
        else:
            # osiagnieto max dlugosc przy tym tempie - przyspieszamy i
            # zaczynamy rosnac od nowa od dlugosci startowej
            self.step_ms = max(cfg.MEMORY_FLASH_ON_MS_MIN,
                                self.step_ms - cfg.MEMORY_SPEEDUP_STEP_MS)
            self.sequence = [random.randrange(cfg.NUM_PADS)
                              for _ in range(cfg.MEMORY_START_LENGTH)]
            self.pause_next_action = "speedup_reset"
        self.pause_started_at = now
        self.state = self.STATE_PAUSE

    def _on_wrong_press(self, now):
        self.lives -= 1
        if self.lives <= 0:
            self._end_game()
            return
        self.pause_next_action = "retry_same"
        self.pause_started_at = now
        self.state = self.STATE_PAUSE

    def _update_pause(self, now):
        if self.pause_next_action == "retry_same":
            duration = cfg.MEMORY_LIFE_LOST_PAUSE_MS
        elif self.pause_next_action == "speedup_reset":
            duration = cfg.MEMORY_SPEEDUP_PAUSE_MS
        else:
            duration = cfg.MEMORY_ROUND_PAUSE_MS
        if now - self.pause_started_at >= duration:
            if self.pause_next_action in ("show_next_round", "retry_same", "speedup_reset"):
                self._begin_showing(now)

    def _end_game(self):
        self.controller.all_off()
        self.state = self.STATE_FINISHED
        self.finished_at = pygame.time.get_ticks()

    def draw(self, screen):
        screen.fill(cfg.BG)

        if self.state == self.STATE_COUNTDOWN:
            ui.draw_pad_grid(screen, self.pad_area, self.led_test_active_pads, {}, {}, self.fonts.small)
            ui.draw_centered_text(screen, str(max(1, self.countdown_value)),
                                   cfg.SCREEN_HEIGHT // 2, self.fonts.huge)
            return

        if self.state == self.STATE_FINISHED:
            ui.draw_centered_text(screen, "KONIEC GRY", 200, self.fonts.title, cfg.TEXT_DARK)
            ui.draw_centered_text(screen, f"Dlugosc sekwencji: {self.score}", 300,
                                   self.fonts.huge, cfg.ACCENT)
            return

        # naglowek: wynik, zycia, tempo
        ui.draw_text(screen, f"Sekwencja: {self.score}", 40, 24, self.fonts.medium)
        lives_text = "Zycia: " + "#" * self.lives + "-" * (cfg.MEMORY_LIVES - self.lives)
        lives_surf = self.fonts.medium.render(lives_text, True, cfg.TEXT_MUTED)
        right_edge = cfg.SCREEN_WIDTH - 40
        screen.blit(lives_surf, (right_edge - lives_surf.get_width(), 24))

        phase_text = "Faza 2: przyspieszenie!" if self.step_ms < cfg.MEMORY_FLASH_ON_MS else "Zapamietaj sekwencje"
        text_color = cfg.TEXT_MUTED
        if self.state == self.STATE_INPUT:
            phase_text = "Twoja kolej!"
        elif self.state == self.STATE_PAUSE:
            if self.pause_next_action == "retry_same":
                phase_text = "Pomylka! Powtarzam te sama sekwencje..."
                text_color = cfg.DANGER
            elif self.pause_next_action == "speedup_reset":
                phase_text = "Super! Przyspieszamy tempo..."
                text_color = cfg.ACCENT
            else:
                phase_text = "Dobrze! Nastepna runda..."
                text_color = cfg.SUCCESS
        ui.draw_centered_text(screen, phase_text, 60, self.fonts.small, text_color)

        active_pads = self._active_show_pads()
        ui.draw_pad_grid(screen, self.pad_area, active_pads,
                          self.correct_flash, self.wrong_flash, self.fonts.small)

        if self.center_flash_color is not None and pygame.time.get_ticks() < self.center_flash_until:
            size = 140
            center_rect = pygame.Rect(0, 0, size, size)
            center_rect.center = self.pad_area.center
            pygame.draw.rect(screen, self.center_flash_color, center_rect, border_radius=16)

        self.stop_button.draw(screen)


class DuelScreen:
    """Tryb 'Pojedynek' (2 graczy, quick-draw): plyta podzielona pionowa
    kreska na lewa/prawa polowe przyciskow. Po losowym opoznieniu zapala
    sie sygnal (wszystkie diody) - kto pierwszy klinie swoim przyciskiem,
    ten ma punkt. Klikniecie przed sygnalem = falszywy start, punkt dla
    przeciwnika. Gra do DUEL_WIN_SCORE punktow."""

    STATE_COUNTDOWN = "countdown"
    STATE_WAITING = "waiting"
    STATE_SIGNAL = "signal"
    STATE_ROUND_PAUSE = "round_pause"
    STATE_FINISHED = "finished"

    def __init__(self, fonts, controller):
        self.fonts = fonts
        self.controller = controller
        self.next_screen = None

        self.state = self.STATE_COUNTDOWN
        self.countdown_start = pygame.time.get_ticks()
        self.countdown_value = 4
        self.LED_TEST_TIERS = [[0, 1], [2, 7], [3, 6], [4, 5]]
        self.led_test_tier_index = -1
        self.led_test_active_pads = set()

        self.score_left = 0
        self.score_right = 0
        self.prev_pressed = [False] * cfg.NUM_PADS

        self.wait_deadline = 0
        self.signal_active_pads = set()
        self.target_pad = None  # konkretny przycisk, ktory trzeba trafic

        self.correct_flash = {}
        self.wrong_flash = {}
        self.flash_left = None   # (kolor, do_kiedy_ms) albo None
        self.flash_right = None

        self.round_message = ""
        self.round_message_color = cfg.TEXT_MUTED
        self.pause_started_at = 0
        self.finished_at = None
        self.winner_side = None

        self.stop_button = ui.Button((cfg.SCREEN_WIDTH - 220, cfg.SCREEN_HEIGHT - 100, 180, 70),
                                      "STOP", fonts.small, bg=cfg.DANGER)
        self.pad_area = pygame.Rect(242, 108, 540, 380)

    @staticmethod
    def _side_of(pad_index):
        return "left" if pad_index in cfg.DUEL_LEFT_PADS else "right"

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.stop_button.is_clicked(event.pos):
            self.controller.all_off()
            self.next_screen = ("menu", 1)

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == self.STATE_COUNTDOWN:
            self._update_countdown(now)
            return
        if self.state == self.STATE_WAITING:
            self._update_waiting(now)
            return
        if self.state == self.STATE_SIGNAL:
            self._update_signal(now)
            return
        if self.state == self.STATE_ROUND_PAUSE:
            self._update_round_pause(now)
            return
        if self.state == self.STATE_FINISHED:
            if now - self.finished_at > 3000:
                self.next_screen = ("menu", 1)
            return

    def _update_countdown(self, now):
        elapsed = now - self.countdown_start
        tier_count = len(self.LED_TEST_TIERS)
        tier_duration = cfg.COUNTDOWN_TIER_MS
        total_duration = tier_duration * tier_count

        tier_index = min(tier_count - 1, elapsed // tier_duration)
        self.countdown_value = tier_count - tier_index

        if tier_index != self.led_test_tier_index:
            for pad in self.led_test_active_pads:
                self.controller.set_led(pad, False)
            self.led_test_tier_index = tier_index
            self.led_test_active_pads = set(self.LED_TEST_TIERS[tier_index])
            for pad in self.led_test_active_pads:
                self.controller.set_led(pad, True)

        if elapsed >= total_duration:
            self.controller.all_off()
            self._start_waiting(now)

    def _start_waiting(self, now):
        self.state = self.STATE_WAITING
        self.wait_deadline = now + random.randint(cfg.DUEL_WAIT_MIN_MS, cfg.DUEL_WAIT_MAX_MS)
        self.target_pad = random.randrange(cfg.NUM_PADS)
        self.prev_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]

    def _check_presses(self):
        """Zwraca indeks pierwszego swiezo wcisnietego przycisku (albo None)."""
        currently_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]
        pressed_index = None
        for i in range(cfg.NUM_PADS):
            if currently_pressed[i] and not self.prev_pressed[i]:
                pressed_index = i
                break
        self.prev_pressed = currently_pressed
        return pressed_index

    def _update_waiting(self, now):
        pressed = self._check_presses()
        if pressed is not None:
            foul_side = self._side_of(pressed)
            self.wrong_flash[pressed] = now + 200
            self._resolve_round(now, winner_side=("right" if foul_side == "left" else "left"),
                                 foul_side=foul_side)
            return
        if now >= self.wait_deadline:
            self.state = self.STATE_SIGNAL
            self.signal_active_pads = {self.target_pad}
            self.controller.set_led(self.target_pad, True)
            self.prev_pressed = [self.controller.is_pressed(i) for i in range(cfg.NUM_PADS)]

    def _update_signal(self, now):
        pressed = self._check_presses()
        if pressed is None:
            return
        if pressed == self.target_pad:
            # trafiony wlasciwy przycisk - wygrywa strona, do ktorej on nalezy
            winner_side = self._side_of(pressed)
            self.correct_flash[pressed] = now + 200
            self._resolve_round(now, winner_side=winner_side, foul_side=None)
        else:
            # zle zgadniety przycisk - to pomylka, punkt dla strony, do ktorej
            # nalezal wlasciwy (swiecacy sie) cel
            foul_side = self._side_of(pressed)
            winner_side = self._side_of(self.target_pad)
            self.wrong_flash[pressed] = now + 200
            self._resolve_round(now, winner_side=winner_side, foul_side=foul_side)

    def _resolve_round(self, now, winner_side, foul_side):
        self.controller.all_off()
        self.signal_active_pads = set()
        if winner_side == "left":
            self.score_left += 1
        else:
            self.score_right += 1

        self.flash_left = None
        self.flash_right = None
        until = now + cfg.DUEL_FLASH_MS
        if foul_side is not None:
            loser_flash = (cfg.DANGER, until)
            winner_flash = (cfg.SUCCESS, until)
            if foul_side == "left":
                self.flash_left, self.flash_right = loser_flash, winner_flash
            else:
                self.flash_right, self.flash_left = loser_flash, winner_flash
            self.round_message = "Falszywy start!"
            self.round_message_color = cfg.DANGER
        else:
            win_flash = (cfg.SUCCESS, until)
            if winner_side == "left":
                self.flash_left = win_flash
            else:
                self.flash_right = win_flash
            self.round_message = "Punkt!"
            self.round_message_color = cfg.SUCCESS

        self.pause_started_at = now
        self.state = self.STATE_ROUND_PAUSE

    def _update_round_pause(self, now):
        if self.flash_left is not None and now >= self.flash_left[1]:
            self.flash_left = None
        if self.flash_right is not None and now >= self.flash_right[1]:
            self.flash_right = None
        self.correct_flash = {k: v for k, v in self.correct_flash.items() if v > now}
        self.wrong_flash = {k: v for k, v in self.wrong_flash.items() if v > now}

        if now - self.pause_started_at >= cfg.DUEL_ROUND_PAUSE_MS:
            if self.score_left >= cfg.DUEL_WIN_SCORE or self.score_right >= cfg.DUEL_WIN_SCORE:
                self.winner_side = "left" if self.score_left > self.score_right else "right"
                self.state = self.STATE_FINISHED
                self.finished_at = now
            else:
                self._start_waiting(now)

    def _draw_half_flash(self, screen):
        half_w = cfg.SCREEN_WIDTH // 2
        for flash, x_offset in ((self.flash_left, 0), (self.flash_right, half_w)):
            if flash is not None:
                color, _until = flash
                overlay = pygame.Surface((half_w, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((*color, 90))
                screen.blit(overlay, (x_offset, 0))

    def draw(self, screen):
        screen.fill(cfg.BG)

        if self.state == self.STATE_COUNTDOWN:
            ui.draw_pad_grid(screen, self.pad_area, self.led_test_active_pads, {}, {}, self.fonts.small)
            ui.draw_centered_text(screen, str(max(1, self.countdown_value)),
                                   cfg.SCREEN_HEIGHT // 2, self.fonts.huge)
            return

        self._draw_half_flash(screen)

        # pionowa kreska dzielaca plyte na strone gracza A i B
        pygame.draw.line(screen, cfg.GRAY, (cfg.SCREEN_WIDTH // 2, 0),
                          (cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT), 4)

        if self.state == self.STATE_FINISHED:
            winner_label = "GRACZ A" if self.winner_side == "left" else "GRACZ B"
            ui.draw_centered_text(screen, f"{winner_label} WYGRYWA!", 220, self.fonts.title, cfg.ACCENT)
            ui.draw_centered_text(screen, f"{self.score_left} : {self.score_right}", 320,
                                   self.fonts.huge, cfg.TEXT_DARK)
            return

        # wyniki, kazdy po swojej stronie
        left_surf = self.fonts.huge.render(str(self.score_left), True, cfg.TEXT_DARK)
        right_surf = self.fonts.huge.render(str(self.score_right), True, cfg.TEXT_DARK)
        screen.blit(left_surf, (cfg.SCREEN_WIDTH // 4 - left_surf.get_width() // 2, 24))
        screen.blit(right_surf, (3 * cfg.SCREEN_WIDTH // 4 - right_surf.get_width() // 2, 24))
        ui.draw_text(screen, "GRACZ A", cfg.SCREEN_WIDTH // 4 - 60, 100, self.fonts.small, cfg.TEXT_MUTED)
        ui.draw_text(screen, "GRACZ B", 3 * cfg.SCREEN_WIDTH // 4 - 60, 100, self.fonts.small, cfg.TEXT_MUTED)

        if self.state == self.STATE_ROUND_PAUSE:
            ui.draw_centered_text(screen, self.round_message, 60, self.fonts.medium, self.round_message_color)
        elif self.state == self.STATE_SIGNAL:
            ui.draw_centered_text(screen, "Trafcie ten przycisk!", 60, self.fonts.medium, cfg.SUCCESS)
        else:
            ui.draw_centered_text(screen, "Czekaj i patrz uwaznie...", 60, self.fonts.medium, cfg.TEXT_MUTED)

        ui.draw_pad_grid(screen, self.pad_area, self.signal_active_pads,
                          self.correct_flash, self.wrong_flash, self.fonts.small)

        self.stop_button.draw(screen)
