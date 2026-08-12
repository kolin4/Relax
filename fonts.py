"""
fonts.py
Tworzenie czcionek uzywanych w calej grze. Musi byc wywolane PO pygame.init().
"""
import pygame


class Fonts:
    def __init__(self):
        self.huge = pygame.font.SysFont("Arial", 70, bold=True)
        self.title = pygame.font.SysFont("Arial", 46, bold=True)
        self.medium = pygame.font.SysFont("Arial", 32, bold=True)
        self.small = pygame.font.SysFont("Arial", 24)
        self.tiny = pygame.font.SysFont("Arial", 18)
        self.digital = pygame.font.SysFont("Courier", 80, bold=True)
