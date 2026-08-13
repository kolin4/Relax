"""
ui.py
Wspólne, wielokrotnego użytku komponenty UI: tekst, karty, przyciski,
klawiatura ekranowa oraz siatka 8 pól odpowiadających fizycznym LED-om.
Dzięki temu każdy ekran gry wygląda spójnie i style zmienia się w jednym
miejscu.
"""
import pygame
import config as cfg


def draw_text(screen, text, x, y, font, color=cfg.TEXT_DARK):
    screen.blit(font.render(text, True, color), (x, y))


def draw_centered_text(screen, text, y, font, color=cfg.TEXT_DARK):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(cfg.SCREEN_WIDTH // 2, y))
    screen.blit(surf, rect)


def draw_card(screen, rect, color=cfg.CARD, radius=16, shadow=True):
    """Rysuje 'kartę' z płaskim cieniem - podstawowy element tła UI."""
    rect = pygame.Rect(rect)
    if shadow:
        shadow_rect = rect.move(0, 5)
        pygame.draw.rect(screen, cfg.GRAY_LIGHT, shadow_rect, border_radius=radius)
    pygame.draw.rect(screen, color, rect, border_radius=radius)


class Button:
    """Klikalny przycisk z zaokrąglonymi rogami i wyśrodkowaną etykietą."""

    def __init__(self, rect, label, font, bg=cfg.ACCENT, fg=cfg.WHITE,
                 bg_active=None, radius=14):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.bg = bg
        self.fg = fg
        self.bg_active = bg_active or bg
        self.radius = radius

    def draw(self, screen, active=False):
        color = self.bg_active if active else self.bg
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        text_surf = self.font.render(self.label, True, self.fg)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class OnScreenKeyboard:
    """Klawiatura ekranowa QWERTY używana do wpisania imienia przy rekordzie."""

    ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

    def __init__(self, font, top=260, key_size=72, spacing=8):
        self.font = font
        self.top = top
        self.key_size = key_size
        self.spacing = spacing
        self.key_rects = []
        self.back_rect = None
        self.ok_rect = None
        self._layout()

    def _layout(self):
        self.key_rects = []
        for row_i, row in enumerate(self.ROWS):
            total_w = len(row) * (self.key_size + self.spacing) - self.spacing
            start_x = (cfg.SCREEN_WIDTH - total_w) // 2
            y = self.top + row_i * (self.key_size + self.spacing)
            for col_i, letter in enumerate(row):
                x = start_x + col_i * (self.key_size + self.spacing)
                self.key_rects.append((pygame.Rect(x, y, self.key_size, self.key_size), letter))

        bottom_y = self.top + len(self.ROWS) * (self.key_size + self.spacing) + 10
        self.back_rect = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 200, bottom_y, 180, 56)
        self.ok_rect = pygame.Rect(cfg.SCREEN_WIDTH // 2 + 20, bottom_y, 180, 56)

    def draw(self, screen):
        for rect, letter in self.key_rects:
            pygame.draw.rect(screen, cfg.GRAY_LIGHT, rect, border_radius=10)
            letter_surf = self.font.render(letter, True, cfg.TEXT_DARK)
            screen.blit(letter_surf, letter_surf.get_rect(center=rect.center))

        pygame.draw.rect(screen, cfg.DANGER, self.back_rect, border_radius=10)
        pygame.draw.rect(screen, cfg.SUCCESS, self.ok_rect, border_radius=10)

        back_surf = self.font.render("USUN", True, cfg.WHITE)
        screen.blit(back_surf, back_surf.get_rect(center=self.back_rect.center))
        ok_surf = self.font.render("OK", True, cfg.WHITE)
        screen.blit(ok_surf, ok_surf.get_rect(center=self.ok_rect.center))

    def handle_click(self, pos):
        """Zwraca literę, 'BACK', 'OK' albo None."""
        if self.back_rect.collidepoint(pos):
            return "BACK"
        if self.ok_rect.collidepoint(pos):
            return "OK"
        for rect, letter in self.key_rects:
            if rect.collidepoint(pos):
                return letter
        return None


def draw_pad_grid(screen, rect, active_pads, correct_flash, wrong_flash, font):
    """
    Rysuje 8 pól odzwierciedlających fizyczny układ przycisków na obudowie:
    jeden przycisk nad wyświetlaczem (1), jeden pod (5), oraz po trzy
    pionowo z każdej strony (2-3-4 po lewej, 8-7-6 po prawej), gdzie
    środkowe przyciski (3 i 7) są wysunięte bardziej na zewnątrz niż
    górny i dolny z tej samej strony. Wszystkie pola mają ten sam rozmiar.

    active_pads: set indeksów (0-7) aktualnie świecących się diod
    correct_flash / wrong_flash: sety indeksów z krótkim błyskiem po trafieniu/pudle
    """
    rect = pygame.Rect(rect)

    # pozycje znormalizowane (0-1) względem obszaru rect, w kolejności
    # indeksów 0-7 odpowiadającej numeracji 1-8 z panelu (zgodnie z ruchem
    # wskazówek zegara: gora, lewy-gorny, lewy-srodkowy, lewy-dolny, dol,
    # prawy-dolny, prawy-srodkowy, prawy-gorny)
    nw, nh = 0.1364, 0.1389
    PAD_LAYOUT = [
        (0.4318, 0.0000),  # 1 - nad wyświetlaczem
        (0.0682, 0.1389),  # 2 - lewy górny
        (0.0000, 0.4306),  # 3 - lewy środkowy (wysunięty)
        (0.0682, 0.7222),  # 4 - lewy dolny
        (0.4318, 0.8611),  # 5 - pod wyświetlaczem
        (0.7955, 0.7222),  # 6 - prawy dolny
        (0.8636, 0.4306),  # 7 - prawy środkowy (wysunięty)
        (0.7955, 0.1389),  # 8 - prawy górny
    ]

    for i, (nx, ny) in enumerate(PAD_LAYOUT):
        x = rect.x + nx * rect.width
        y = rect.y + ny * rect.height
        w = nw * rect.width
        h = nh * rect.height
        pad_rect = pygame.Rect(x, y, w, h)

        base_color = cfg.PAD_COLORS[i]
        if i in correct_flash:
            fill = cfg.SUCCESS
        elif i in wrong_flash:
            fill = cfg.DANGER
        elif i in active_pads:
            fill = base_color
        else:
            fill = cfg.GRAY_LIGHT

        pygame.draw.rect(screen, fill, pad_rect, border_radius=14)
        if i in active_pads:
            pygame.draw.rect(screen, cfg.WHITE, pad_rect, width=4, border_radius=14)

        label_color = cfg.TEXT_DARK if fill == cfg.GRAY_LIGHT else cfg.WHITE
        label = font.render(str(i + 1), True, label_color)
        screen.blit(label, label.get_rect(center=pad_rect.center))
