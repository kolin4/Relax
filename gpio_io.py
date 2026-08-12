"""
gpio_io.py
Warstwa abstrakcji nad sprzętem: 8 par (przycisk, dioda LED).

Na Raspberry Pi korzysta z prawdziwego RPi.GPIO. Jeśli moduł nie jest
dostępny (np. testujesz grę na zwykłym komputerze przy pisaniu kodu),
automatycznie przełącza się w tryb symulacji: przyciski 1-8 na klawiaturze
zastępują fizyczne przyciski, a stan diod jest tylko śledzony wewnętrznie
(przydatne np. do testowania UI bez podłączonego sprzętu).
"""
import pygame

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except (ImportError, RuntimeError):
    HARDWARE_AVAILABLE = False


class ButtonLedController:
    """Odczyt przycisków i sterowanie diodami LED, niezależnie od platformy."""

    # klawisze zastępcze używane w trybie symulacji (bez GPIO)
    SIM_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]

    def __init__(self, button_pins, led_pins):
        if len(button_pins) != len(led_pins):
            raise ValueError("Liczba przycisków i diod LED musi być taka sama")
        self.button_pins = button_pins
        self.led_pins = led_pins
        self.count = len(button_pins)
        self.hardware = HARDWARE_AVAILABLE
        self._led_state = [False] * self.count

        if self.hardware:
            GPIO.setmode(GPIO.BCM)
            for bp in button_pins:
                GPIO.setup(bp, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            for lp in led_pins:
                GPIO.setup(lp, GPIO.OUT)
                GPIO.output(lp, False)
        else:
            print("[gpio_io] RPi.GPIO niedostepne - tryb symulacji klawiatura (klawisze 1-8) aktywny.")

    def is_pressed(self, index):
        """True, jesli przycisk o danym indeksie (0-7) jest wcisniety."""
        if self.hardware:
            return GPIO.input(self.button_pins[index]) == GPIO.LOW
        keys = pygame.key.get_pressed()
        return keys[self.SIM_KEYS[index]]

    def set_led(self, index, state):
        """Zapala (True) lub gasi (False) diode o danym indeksie."""
        self._led_state[index] = state
        if self.hardware:
            GPIO.output(self.led_pins[index], state)

    def led_state(self, index):
        return self._led_state[index]

    def all_off(self):
        for i in range(self.count):
            self.set_led(i, False)

    def cleanup(self):
        self.all_off()
        if self.hardware:
            GPIO.cleanup()
