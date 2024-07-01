#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""The example I wrote while working with Kurt on 2024-06-19

Updated example on 2024-07-01
"""

from pathlib import Path
import pygame
from pygame import Color
import sys
import atexit
import random

def shutdown():
    print("Shutdown")
    pygame.quit()

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Example")
        pygame.mouse.set_visible(True)
        self.surf = pygame.display.set_mode((600,500), flags=pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

    def run(self):
        while True: self.game_loop()

    def game_loop(self):
        # UI
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_2: print("2")
                        case pygame.K_q: sys.exit()

        # Make stuff
        (x,y) = pygame.mouse.get_pos()
        s = 100
        r = max(2,s/10)
        points = [[x - s, y - s],
                  [x - s, y + s],
                  [x + s, y + s]]

        for p in points:
            p[0] = p[0] + random.uniform(-r,r)
            p[1] = p[1] + random.uniform(-r,r)

        # Render stuff
        self.surf.fill(Color(0,0,0))
        pygame.draw.polygon(self.surf, Color(0,0,255), points)
        pygame.display.update()

        # Clock - regulate how FAST this loop runs
        self.clock.tick(60)                             # Run game at 60FPS

if __name__ == '__main__':
    print(f"Run {Path(__file__).name}")
    atexit.register(shutdown)
    Game().run()
