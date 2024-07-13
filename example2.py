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
[x] make a Player class: track position in a debug rect, but draw as a wiggling polygon rect
[x] make a TileMap class: move wall code to TileMap
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
    def __init__(self, size:int) -> None:
        self.font = pygame.font.SysFont("RobotoMono", size)
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
    def __init__(self, game, size:int=15) -> None:
        super().__init__(size)
        self.game = game
        self.msg += f"FPS: {self.game.clock.get_fps():0.0f}"
        self.msg += f" | dt: {self.game.dt}"
        self.msg += f" | Window: {self.game.os_window.get_size()}"

class Player:
    def __init__(self, game):
        self.game = game
        self.pos = [0,0]                                # Initial position (topleft of self.debug_rect) on the screen
        self.old_pos = (0,0)                            # Track player's previous position
        # self.size = (50,80)                             # Player initial w,h
        self.size = (self.game.tile_size*2,self.game.tile_size*2) # Player initial w,h
        self.debug_rect = Rect(self.pos, self.size)     # White outline, updated in 'animate()'
        self._reset_art()                               # Set art polygon points equal to debug_rect
        self.dt = 0                                     # Track how much time has elapsed for animations
        self.period = 50                               # ms: Update animation each period
        self.wiggle = 3                                 # Animation wiggles each vertex +/- self.wiggle pixels

    def _reset_art(self) -> None:
        self.art = [list(self.debug_rect.topleft),
                    list(self.debug_rect.topright),
                    list(self.debug_rect.bottomright),
                    list(self.debug_rect.bottomleft)]

    def animate(self) -> None:
        if self.game.text_hud:
            self.game.text_hud.msg += f"\nPlayer pos: {self.pos}"

        # Update position
        self.debug_rect = Rect(self.pos, self.size)     # Update the debug rect (white outline)
        def update_art_position():
            offset = (self.pos[0] - self.old_pos[0], self.pos[1] - self.old_pos[1])
            self.old_pos = (self.pos[0], self.pos[1])   # Update old_pos to latest position
            self.art[0][0] += offset[0]
            self.art[1][0] += offset[0]
            self.art[2][0] += offset[0]
            self.art[3][0] += offset[0]
            self.art[0][1] += offset[1]
            self.art[1][1] += offset[1]
            self.art[2][1] += offset[1]
            self.art[3][1] += offset[1]
        update_art_position()                           # Update the polygon (red filled)

        # Animate the polygon
        self.dt += self.game.dt                         # Add elapsed time
        if self.dt >= self.period:                      # Check if it's time to update the animation
            self.dt = 0                                 # Reset the elapsed time
            self._reset_art()                           # Reset all vertices to match the debug_rect
            w = self.wiggle                             # Wiggle amount
            self.art[0][0] += random.uniform(-w,w)
            self.art[0][1] += random.uniform(-w,w)
            self.art[1][0] += random.uniform(-w,w)
            self.art[1][1] += random.uniform(-w,w)
            self.art[2][0] += random.uniform(-w,w)
            self.art[2][1] += random.uniform(-w,w)
            self.art[3][0] += random.uniform(-w,w)
            self.art[3][1] += random.uniform(-w,w)

class TileMap:
    def __init__(self, game):
        self.game = game
        self.make_tiles()

    def make_tiles(self) -> None:
        """Create a list of tiles in self.tiles.

        Each tile is a dict: {'rect':Rect, 'color':Color}.
        """
        self.tiles = []
        def make_wall_vertical(color, tile_size, x, ystart, num_tiles):
            """Make a vertical wall at 'x', starting at 'ystart' and extending down 'num_tiles'."""
            n = 0
            while n < num_tiles:
                self.tiles.append({
                    'rect':Rect((x,tile_size*n),(tile_size,tile_size)),
                    'color':color})
                n += 1
        def make_wall_horizontal(color, tile_size, y, xstart, num_tiles):
            """Make a horizontal wall at 'y', starting at 'xstart' and extending right 'num_tiles'."""
            n = 0
            while n < num_tiles:
                self.tiles.append({
                    'rect':Rect((tile_size*n,y),(tile_size,tile_size)),
                    'color':color})
                n += 1
        window_width, window_height = self.game.os_window.get_size()
        tile_size = self.game.tile_size
        num_horiz = math.ceil(window_width/tile_size)
        left=0; top=0; right=window_width-tile_size; bottom = window_height-tile_size
        make_wall_vertical(Color(255,200,0), tile_size,   x=left,   ystart=top,  num_tiles=math.ceil(window_height/tile_size))
        make_wall_vertical(Color(0,200,0), tile_size,   x=right,  ystart=top,  num_tiles=math.ceil(window_height/tile_size))
        make_wall_horizontal(Color(0,200,200), tile_size, y=top,    xstart=left, num_tiles=math.ceil(window_width/tile_size))
        make_wall_horizontal(Color(255,0,200), tile_size, y=bottom, xstart=left, num_tiles=math.ceil(window_width/tile_size))

    def render(self, surf:pygame.Surface) -> None:
        for tile in self.tiles:
            pygame.draw.rect(surf, tile['color'], tile['rect'])

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.os_window = pygame.display.set_mode((16*50,9*50), flags=pygame.RESIZABLE)
        pygame.display.set_caption("Collisions")
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.tile_size = 25
        self.tile_map = TileMap(self)
        self.player = Player(self)
        self.debug = True

    def run(self):
        while True: self.game_loop()

    def KEYDOWN(self, event):
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_w:
                self.player.pos[1] -= self.tile_size
            case pygame.K_a:
                self.player.pos[0] -= self.tile_size
            case pygame.K_s:
                self.player.pos[1] += self.tile_size
            case pygame.K_d:
                self.player.pos[0] += self.tile_size
            case pygame.K_F2:
                self.debug = not self.debug

    def game_loop(self):
        self.handle_events()
        self.text_hud = TextHud(self, size=20) if self.debug else None
        self.player_update()
        self.render()
        self.clock.tick(60)
        self.dt = self.clock.get_time()

    def render(self):
        self.os_window.fill(Color(30,30,30)) # Erases window
        pygame.draw.polygon(self.os_window, Color(255,0,0), self.player.art) # Draw player
        if self.debug:
            pygame.draw.rect(self.os_window, Color(255,255,255), self.player.debug_rect, width=1) # Draw player
        self.tile_map.render(self.os_window)
        if self.debug: self.text_hud.render(self.os_window, Color(255,255,255))
        pygame.display.update() # Final render

    def draw_walls(self):
        # Draw East Wall
        tile_size = self.tile_size
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
        self.player.animate()


if __name__ == '__main__':
    logger = setup_logging()
    logger.info(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    game = Game()
    game.run()
