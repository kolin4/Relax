"""
config.py
Wszystkie stałe konfiguracyjne gry w jednym miejscu: rozmiar ekranu,
piny GPIO, poziomy trudności, ścieżki do wyników i paleta kolorów UI.
Zmiana rozgrywki (np. liczby przycisków, czasów reakcji) zaczyna się tutaj.
"""
import os

# === Ekran ===
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FPS = 60

# === GPIO: 8 przycisków + 8 diod LED ===
# Piny BCM dobrane tak, by nie kolidować z I2C (2,3), UART (14,15) ani SPI.
BUTTON_PINS = [5, 6, 13, 19, 26, 21, 20, 16]
LED_PINS    = [17, 27, 22, 23, 24, 25, 12, 4]
NUM_PADS = len(BUTTON_PINS)

# === Rozgrywka ===
GAME_DURATION = 60          # czas jednej rundy w sekundach
MAX_COMBO_MULTIPLIER = 3.0
COMBO_STEP = 0.5
COMBO_HITS_PER_STEP = 3     # co ile trafień z rzędu rośnie mnożnik punktów

# poziom -> (czas reakcji w ms, ile diod może świecić się jednocześnie)
LEVEL_TIMINGS = {
    1: (1000, 1),
    2: (800, 1),
    3: (650, 1),
    4: (500, 2),
    5: (350, 2),
}
NUM_LEVELS = len(LEVEL_TIMINGS)

# === Wyniki ===
SCORES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wyniki")
MAX_HIGHSCORES = 10
MAX_NAME_LENGTH = 10

# === Paleta kolorów UI (jasny, płaski motyw) ===
BG = (245, 247, 250)
CARD = (255, 255, 255)
TEXT_DARK = (35, 38, 45)
TEXT_MUTED = (120, 128, 140)
ACCENT = (0, 122, 255)
ACCENT_DARK = (0, 90, 200)
SUCCESS = (40, 180, 99)
DANGER = (220, 60, 60)
WARNING = (240, 170, 30)
GRAY_LIGHT = (225, 228, 233)
GRAY = (190, 195, 202)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

# 8 unikalnych kolorów - każde pole/dioda ma swoją barwę, gdy aktywna
PAD_COLORS = [
    (255, 99, 99), (255, 170, 60), (255, 221, 89), (120, 220, 120),
    (90, 200, 220), (100, 140, 240), (170, 120, 240), (240, 120, 200),
]
