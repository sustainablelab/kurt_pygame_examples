#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Programming with Kurt

[x] draw a rect
[x] move the rect
[ ] control size with a key
[ ] draw walls
[ ] collide with the walls
"""

from pathlib import Path
import atexit
import sys                                              # sys.exit()
import pygame
from pygame import Color, Rect
import random

def shutdown(filename:str):
    print(f"Shutdown {filename}")
    pygame.font.quit()
    pygame.quit()

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.os_window = pygame.display.set_mode((16*50,9*50), flags=pygame.RESIZABLE)
        pygame.display.set_caption("bob")

        self.clock = pygame.time.Clock()

    def run(self):
        self.pos = [0,0]
        while True: self.game_loop()

    def KEYDOWN(self, event):
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_w:
                self.pos[1] -= 10
            case pygame.K_a:
                self.pos[0] -= 10
            case pygame.K_s:
                self.pos[1] += 10
            case pygame.K_d:
                self.pos[0] += 10


    def game_loop(self):
        rx = random.uniform(-5,5)
        ry = random.uniform(-5,5)
        self.pos
        self.rect = Rect( (self.pos[0]-rx/2, self.pos[1]-ry/2), (50 + rx,80 + ry))
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)

        self.os_window.fill(Color(30,30,30))
        pygame.draw.rect(self.os_window, Color(255,0,0), self.rect)
        # Draw stuff
        
        # Render
        pygame.display.update()

        self.clock.tick(60)

if __name__ == '__main__':
    print(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    game = Game()
    game.run()
