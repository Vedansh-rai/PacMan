import pygame
import sys
import random
import time
import os
from collections import deque
from pygame import mixer

# Initialize pygame with larger audio buffer to prevent sound lag
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
mixer.init()

# Constants
CELL_SIZE = 40
TEXT_AREA_WIDTH = 250
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
PINK = (255, 192, 203)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 139)

class GameAudio:
    def __init__(self):
        """Initialize all game sounds and music"""
        # Create sounds directory if it doesn't exist
        if not os.path.exists('sounds'):
            os.makedirs('sounds')
            
        # Initialize all sound effects
        self.sounds = {
            'point': self.load_sound('point.wav', volume=0.5),
            'power': self.load_sound('power.wav', volume=0.6),
            'death': self.load_sound('death.wav', volume=0.7),
            'win': self.load_sound('win.wav', volume=0.7),
            'ghost': self.load_sound('ghost.wav', volume=0.6),
            'move': self.load_sound('move.wav', volume=0.3),
            'start': self.load_sound('start.wav', volume=0.7)
        }
        
        # Initialize background music
        self.music_loaded = False
        try:
            mixer.music.load('sounds/background.mp3')
            mixer.music.set_volume(0.4)
            self.music_loaded = True
        except:
            print("Background music not found")
    
    def load_sound(self, filename, volume=0.5):
        """Helper function to load a sound with error handling"""
        try:
            sound = mixer.Sound(f'sounds/{filename}')
            sound.set_volume(volume)
            return sound
        except:
            print(f"Sound {filename} not found")
            class DummySound:
                def play(self): pass
            return DummySound()
    
    def play_sound(self, sound_name):
        """Play a sound effect by name"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def start_music(self):
        """Start background music (looped)"""
        if self.music_loaded:
            mixer.music.play(-1)
    
    def stop_music(self):
        """Stop background music"""
        if self.music_loaded:
            mixer.music.stop()

class GameState:
    def __init__(self):
        self.mode = "moderate"
        self.maze = []
        self.pacman_pos = (1, 1)
        self.goal_pos = (13, 8)
        self.ghosts = []
        self.points = []
        self.big_stars = []
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.won = False
        self.screen = None
        self.ghost_direction = []
        self.pacman_direction = (0, 0)
        self.last_move_time = 0
        self.ghost_move_time = 0
        self.power_up_time = 0
        self.power_up_active = False
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        # Initialize audio system
        self.audio = GameAudio()
        self.initialize_game()

    def initialize_game(self):
        if self.mode == "easy":
            self.setup_easy_mode()
        elif self.mode == "moderate":
            self.setup_moderate_mode()
        else:
            self.setup_advanced_mode()
        
        self.ghost_direction = [(random.choice([-1, 1]), 0) for _ in range(len(self.ghosts))]
        self.pacman_direction = (0, 0)
        self.last_move_time = time.time()
        self.ghost_move_time = time.time()
        self.power_up_time = 0
        self.power_up_active = False
        
        # Play start sound and background music
        self.audio.play_sound('start')
        self.audio.start_music()

    # [Keep all other methods the same until move_pacman]

    def move_pacman(self, dx, dy):
        if self.game_over:
            return

        current_time = time.time()
        if current_time - self.last_move_time < 0.2:
            return
            
        self.last_move_time = current_time
        
        new_x, new_y = self.pacman_pos[0] + dx, self.pacman_pos[1] + dy
        rows = len(self.maze)
        cols = len(self.maze[0]) if rows > 0 else 0

        if 0 <= new_x < cols and 0 <= new_y < rows and self.maze[new_y][new_x] == 0:
            self.pacman_pos = (new_x, new_y)
            self.pacman_direction = (dx, dy)
            self.audio.play_sound('move')  # Play movement sound

            if self.pacman_pos in self.points:
                self.points.remove(self.pacman_pos)
                self.score += 10
                self.audio.play_sound('point')

            if self.pacman_pos in self.big_stars:
                self.big_stars.remove(self.pacman_pos)
                self.score += 50
                self.power_up_active = True
                self.power_up_time = time.time()
                self.audio.play_sound('power')

            if self.pacman_pos == self.goal_pos:
                self.game_over = True
                self.won = True
                self.audio.play_sound('win')
                self.audio.stop_music()

    def check_collisions(self):
        if self.game_over:
            return

        if self.power_up_active and time.time() - self.power_up_time > 10:
            self.power_up_active = False

        if self.pacman_pos in self.ghosts:
            if self.power_up_active:
                ghost_index = self.ghosts.index(self.pacman_pos)
                self.ghosts.pop(ghost_index)
                self.ghost_direction.pop(ghost_index)
                self.score += 100
                self.audio.play_sound('ghost')
            else:
                self.lives -= 1
                self.audio.play_sound('death')
                if self.lives <= 0:
                    self.game_over = True
                    self.won = False
                    self.audio.stop_music()
                else:
                    self.pacman_pos = (1, 1)
                    valid_positions = [p for p in self.get_valid_positions()
                                      if p != self.pacman_pos
                                      and p != self.goal_pos
                                      and p not in self.big_stars]
                    if valid_positions:
                        for i in range(len(self.ghosts)):
                            self.ghosts[i] = random.choice(valid_positions)
                    self.pacman_direction = (0, 0)

    # [Keep all other methods exactly the same as in your original code]

def main():
    clock = pygame.time.Clock()
    game = GameState()

    # [Rest of your main() function remains exactly the same]

if __name__ == "__main__":
    main()