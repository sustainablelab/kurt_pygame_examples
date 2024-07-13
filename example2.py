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
[x] Update Player and TileMap to use game coordinates instead of pixel coordinates
[x] draw TileMap as boxes during debug
[x] save TileMap to file as JSON -- required replacing Rect and Color with tuples.
"""

from pathlib import Path
import atexit
import sys                                              # sys.exit()
import pygame
from pygame import Color, Rect
import random
import math
import logging
import json

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
        winsize = self.game.os_window.get_size()
        self.msg += f"\nWindow: g{self.game.xfm.pg(winsize)} p{winsize}"
        mpos = pygame.mouse.get_pos()
        self.msg += f" | Mouse: g{self.game.xfm.pg(mpos)} p{mpos}"

class Player:
    def __init__(self, game):
        self.game = game
        self.pos = [1,1]                                # Initial position (topleft) in game coordinates
        self.old_pos = self.game.xfm.gp(self.pos)       # Track player's previous position in pixel coordinates
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
        # Update position
        pos = self.game.xfm.gp(self.pos)                # Xfm player position to pixel coordinates
        if self.game.text_hud:
            self.game.text_hud.msg += f"\nPlayer pos: {self.pos} ({pos})"

        self.debug_rect = Rect(pos, self.size)     # Update the debug rect (white outline)
        def update_art_position(pos):
            offset = (pos[0] - self.old_pos[0], pos[1] - self.old_pos[1])
            self.old_pos = (pos[0], pos[1])   # Update old_pos to latest position
            self.art[0][0] += offset[0]
            self.art[1][0] += offset[0]
            self.art[2][0] += offset[0]
            self.art[3][0] += offset[0]
            self.art[0][1] += offset[1]
            self.art[1][1] += offset[1]
            self.art[2][1] += offset[1]
            self.art[3][1] += offset[1]
        update_art_position(pos)                        # Update the polygon (red filled) to new pos on screen

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
        """Create a dict of tiles in self.tiles.

        Each tile is a dict: {'rect':Rect, 'color':Color}.
        """
        self.tiles = {}
        def make_wall_vertical(color, tile_size, x, num_tiles):
            """Make a vertical wall at 'x', starting at y=0 and extending down 'num_tiles'."""
            size = (tile_size, tile_size)               # All tiles are the same size
            n = 0
            while n < num_tiles:
                topleft = (x,tile_size*n)               # Position in pixel coordinates
                pos = self.game.xfm.pg(topleft)         # Position in game coordinates
                name = f"({pos[0]},{pos[1]})"           # Name tiles by their position
                # self.tiles[name] = {'rect':Rect(topleft,size), 'color':color}
                # self.tiles[name] = {'rect':{'topleft':topleft,'size':size}, 'color':color}
                self.tiles[name] = {'rect':{'topleft':topleft,'size':size},
                                    'color':(color.r,color.g,color.b)}
                n += 1
        def make_wall_horizontal(color, tile_size, y, num_tiles):
            """Make a horizontal wall at 'y', starting at x=0 and extending right 'num_tiles'."""
            size = (tile_size, tile_size)               # All tiles are the same size
            n = 0
            while n < num_tiles:
                topleft = (tile_size*n,y)               # Position in pixel coordinates
                pos = self.game.xfm.pg(topleft)         # Position in game coordinates
                name = f"({pos[0]},{pos[1]})"           # Name tiles by their position
                self.tiles[name] = {'rect':{'topleft':topleft,'size':size},
                                    'color':(color.r,color.g,color.b)}
                n += 1
        window_width, window_height = self.game.os_window.get_size()
        tile_size = self.game.tile_size
        left=0; top=0; right=window_width-tile_size; bottom = window_height-tile_size
        make_wall_vertical(Color(255,200,0),  tile_size,x=left,  num_tiles=math.ceil(window_height/tile_size))
        make_wall_vertical(Color(0,200,0),    tile_size,x=right, num_tiles=math.ceil(window_height/tile_size))
        make_wall_horizontal(Color(0,200,200),tile_size,y=top,   num_tiles=math.ceil(window_width/tile_size))
        make_wall_horizontal(Color(255,0,200),tile_size,y=bottom,num_tiles=math.ceil(window_width/tile_size))

    def make_tiles_old(self) -> None:
        """Create a list of tiles in self.tiles.

        Each tile is a dict: {'rect':Rect, 'color':Color}.
        """
        self.tiles = []
        def make_wall_vertical(color, tile_size, x, num_tiles):
            """Make a vertical wall at 'x', starting at y=0 and extending down 'num_tiles'."""
            n = 0
            while n < num_tiles:
                self.tiles.append({
                    'rect':Rect((x,tile_size*n),(tile_size,tile_size)),
                    'color':color})
                n += 1
        def make_wall_horizontal(color, tile_size, y, num_tiles):
            """Make a horizontal wall at 'y', starting at x=0 and extending right 'num_tiles'."""
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
        make_wall_vertical(Color(255,   200, 0),   tile_size, x=left,   num_tiles=math.ceil(window_height/tile_size))
        make_wall_vertical(Color(0,     200, 0),   tile_size, x=right,  num_tiles=math.ceil(window_height/tile_size))
        make_wall_horizontal(Color(0,   200, 200), tile_size, y=top,    num_tiles=math.ceil(window_width/tile_size))
        make_wall_horizontal(Color(255, 0,   200), tile_size, y=bottom, num_tiles=math.ceil(window_width/tile_size))

    def render_old(self, surf:pygame.Surface) -> None:
        for tile in self.tiles:
            pygame.draw.rect(surf, tile['color'], tile['rect'])

    def render(self, surf:pygame.Surface) -> None:
        for name in self.tiles:
            color = Color(self.tiles[name]['color'])
            # rect = self.tiles[name]['rect']
            topleft = self.tiles[name]['rect']['topleft']
            size = self.tiles[name]['rect']['size']
            rect = Rect(topleft,size)
            width = int(self.game.tile_size/10) if self.game.debug else 0
            pygame.draw.rect(surf, color, rect, width)

class Xfm:
    def __init__(self, game):
        self.game = game

    def pg(self, p:tuple) -> tuple:
        return (round(p[0]/self.game.tile_size), round(p[1]/self.game.tile_size))

    def gp(self, p:tuple) -> tuple:
        return (p[0]*self.game.tile_size, p[1]*self.game.tile_size)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.save_file = "level.json"  # To pretty print "level.json": $ python -m json.tool level.json
        self.os_window = pygame.display.set_mode((16*50,9*50), flags=pygame.RESIZABLE)
        pygame.display.set_caption("Collisions")
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.xfm = Xfm(self)
        self.tile_size = 50
        self.tile_map = TileMap(self)
        self.player = Player(self)
        self.debug = True

    def run(self):
        while True: self.game_loop()

    def KEYDOWN(self, event):
        kmod = pygame.key.get_mods()
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_w:
                self.player.pos[1] -= 1
            case pygame.K_a:
                self.player.pos[0] -= 1
            case pygame.K_s:
                if (kmod & pygame.KMOD_CTRL):
                    logger.debug(f"Saved tile map to \"{self.save_file}\"")
                    with open(self.save_file, 'w') as fp:
                        json.dump(self.tile_map.tiles, fp)
                else:
                    self.player.pos[1] += 1
            case pygame.K_d:
                self.player.pos[0] += 1
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

    def handle_events(self):
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)
                case pygame.WINDOWRESIZED:
                    self.tile_map.make_tiles() # Resize the walls to match the window

    def player_update(self) -> None:
        self.player.animate()

if __name__ == '__main__':
    logger = setup_logging()
    logger.info(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    game = Game()
    game.run()
