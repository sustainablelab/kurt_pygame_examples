#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Programming with Kurt

[x] draw a rect
[x] move the rect
[x] add a HUD
[ ] control size with a key
[x] set up logging
[x] draw walls
[ ] collide with the walls
"""

from pathlib import Path
import atexit
import sys                                              # sys.exit()
import pygame
from pygame import Color, Rect
import random
import math
import logging

def setup_logging(loglevel:str = "DEBUG") -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            "%(asctime)s %(levelname)s in '%(funcName)s()' (%(filename)s:%(lineno)d) -- %(message)s",
            datefmt="%H:%M:%S")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(loglevel)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

def shutdown(filename:str):
    logger.info(f"Shutdown {filename}")
    pygame.font.quit()
    pygame.quit()

class Text:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont("RobotoMono", 50)
        self.pos = (0,0)
        self.msg = ""

    def render(self, surf:pygame.Surface, color:Color) -> None:
        ### pygame.font.Font.get_linesize()
        line_space = self.font.get_linesize()
        lines = self.msg.split("\n")
        for i,line in enumerate(lines):
            ### render(text, antialias, color, background=None) -> Surface
            text_surf = self.font.render(line, True, color)
            ### blit(source, dest, area=None, special_flags=0) -> Rect
            surf.blit(text_surf, (self.pos[0],self.pos[1] + i*line_space))

class TextHud(Text):
    def __init__(self, game) -> None:
        super().__init__()
        self.game = game
        self.msg += f"FPS: {self.game.clock.get_fps():0.0f}"
        self.msg += f"\nWindow: {self.game.os_window.get_size()}"

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
        self.text_hud = TextHud(self)
        self.player_update()
        self.handle_events()
        self.render()
        self.clock.tick(60)

    def render(self):
        self.os_window.fill(Color(30,30,30)) # Erases window
        pygame.draw.rect(self.os_window, Color(255,0,0), self.rect) # Draw player
        self.draw_walls()
        self.text_hud.render(self.os_window, Color(255,255,255))
        pygame.display.update() # Final render

    def draw_vertical(self, color:Color, tile_size, x) -> None:
        n = 0
        tiles = []
        window_height = self.os_window.get_size()[1]
        num_tiles = math.ceil(window_height/tile_size)
        while n < num_tiles:
            tiles.append( Rect((x,tile_size*n), (tile_size,tile_size)))
            n += 1
        for tile in tiles:
            pygame.draw.rect(self.os_window, color, tile)

    def draw_horizontal(self, color:Color, tile_size, y, use_hud:bool=False) -> None:
        n = 0
        tiles = []
        window_width = self.os_window.get_size()[0]
        num_tiles = math.ceil(window_width/tile_size)
        while n < num_tiles:
            tiles.append( Rect((tile_size*n, y), (tile_size,tile_size)))
            n += 1
        for tile in tiles:
            pygame.draw.rect(self.os_window, color, tile)
        if use_hud: self.text_hud.msg += f"\nnum_tiles: {num_tiles}"

    def draw_walls(self):
        # Draw East Wall
        tile_size = 25
        window_width = self.os_window.get_size()[0]
        window_height = self.os_window.get_size()[1]
        self.draw_vertical(Color(255,200,0), tile_size, x=window_width - tile_size) # East wall
        self.draw_vertical(Color(0,200,0),tile_size, x=0) # West wall
        self.draw_horizontal(Color(0,200,200),tile_size, y=window_height - tile_size) # South wall
        self.draw_horizontal(Color(255,0,200),tile_size, y=0, use_hud=True) # North wall

    def handle_events(self):
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)


    def player_update(self) -> None:
        rx = random.uniform(-5,5)
        ry = random.uniform(-5,5)
        self.rect = Rect( (self.pos[0]-rx/2, self.pos[1]-ry/2), (50 + rx,80 + ry))


if __name__ == '__main__':
    logger = setup_logging()
    logger.info(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    game = Game()
    game.run()
