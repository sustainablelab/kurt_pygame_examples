#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Programming with Kurt

[x] draw a rect
[x] move the rect
[x] add a HUD
[ ] control size with a key
[x] set up logging
[x] draw walls
[x] collide with the walls
[x] make a Player class: track position in a debug rect, but draw as a wiggling polygon rect
[x] make a TileMap class: move wall code to TileMap
[x] Update Player and TileMap to use game coordinates instead of pixel coordinates
[x] draw TileMap as boxes during debug
[x] save TileMap to file as JSON -- required replacing Rect and Color with tuples.
[x] TileMap tracks whether a tile can collide
[x] create a "load level" menu
[ ] load tilemap level from file (select file from "load level" menu)
[ ] add "is_push" behavior to TileMap tiles
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
import os

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

    @property
    def width(self) -> int:
        """Return the width of the rendered text."""
        return self.font.size(self.msg)[0]

    @property
    def linesize(self) -> int:
        """Return the vertical distance fromm top of one line to top of next line."""
        return self.font.get_linesize()

    def center_x(self, rect:pygame.Rect) -> int:
        """Return the x-value to horizontally center the text in the 'rect'."""
        return int(rect.left + (rect.width-self.width)/2)

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

    def is_collision(self, pos:tuple) -> bool:
        """Check if player collides with TileMap.

        Check for collisions at all four tiles that make up the player.
        """
        collision = False
        tiles = [(pos[0],   pos[1]),   # topleft
                 (pos[0]+1, pos[1]),   # topright
                 (pos[0],   pos[1]+1), # bottomleft
                 (pos[0]+1, pos[1]+1)] # bottomright
        for tile in tiles:
            name = f"({tile[0]},{tile[1]})"
            if name in self.game.tile_map.tiles:
                if self.game.tile_map.tiles[name]['collides']:
                    collision = True
                    break
        return collision

    def move_up(self) -> None:
        self.pos[1] -= 1
        if self.is_collision(self.pos): self.pos[1] += 1

    def move_left(self) -> None:
        self.pos[0] -= 1
        if self.is_collision(self.pos): self.pos[0] += 1

    def move_down(self) -> None:
        self.pos[1] += 1
        if self.is_collision(self.pos): self.pos[1] -= 1

    def move_right(self) -> None:
        self.pos[0] += 1
        if self.is_collision(self.pos): self.pos[0] -= 1

class TileMap:
    def __init__(self, game):
        self.game = game
        self.make_tiles()

    def add_tile(self, name:str, topleft:tuple, size:tuple, color:Color, collides:bool) -> None:
        """Add dict of serialized tile data to self.tiles."""
        self.tiles[name] = {'rect':{'topleft':topleft,'size':size},
                            'color':(color.r,color.g,color.b),
                            'collides':collides}

    def make_tiles(self) -> None:
        """Create a dict of tiles in self.tiles.

        Each tile is a dict:
            {"(0,0)":                   # tile "key" is its position as a string
                {"rect":                # value is another dict
                    {"topleft": [0, 0],
                     "size": [50, 50]},
                     "color": [0, 200, 200]},
            "(0,1)":
                {...
        """
        self.tiles = {}
        def make_wall_vertical(color, tile_size, x, num_tiles, collides):
            """Make a vertical wall at 'x', starting at y=0 and extending down 'num_tiles'."""
            size = (tile_size, tile_size)               # All tiles are the same size
            n = 0
            while n < num_tiles:
                topleft = (x,tile_size*n)               # Position in pixel coordinates
                pos = self.game.xfm.pg(topleft)         # Position in game coordinates
                name = f"({pos[0]},{pos[1]})"           # Name tiles by their position
                self.add_tile(name, topleft, size, color, collides)
                n += 1
        def make_wall_horizontal(color, tile_size, y, num_tiles, collides):
            """Make a horizontal wall at 'y', starting at x=0 and extending right 'num_tiles'."""
            size = (tile_size, tile_size)               # All tiles are the same size
            n = 0
            while n < num_tiles:
                topleft = (tile_size*n,y)               # Position in pixel coordinates
                pos = self.game.xfm.pg(topleft)         # Position in game coordinates
                name = f"({pos[0]},{pos[1]})"           # Name tiles by their position
                self.add_tile(name, topleft, size, color, collides)
                n += 1
        window_width, window_height = self.game.os_window.get_size()
        tile_size = self.game.tile_size
        left=0; top=0; right=window_width-tile_size; bottom = window_height-tile_size
        make_wall_vertical(Color(255,200,0),  tile_size,x=left,  num_tiles=math.ceil(window_height/tile_size), collides=True)
        make_wall_vertical(Color(0,200,0),    tile_size,x=right, num_tiles=math.ceil(window_height/tile_size), collides=True)
        make_wall_horizontal(Color(0,200,200),tile_size,y=top,   num_tiles=math.ceil(window_width/tile_size),  collides=True)
        make_wall_horizontal(Color(255,0,200),tile_size,y=bottom,num_tiles=math.ceil(window_width/tile_size),  collides=True)

    def make_tiles_old(self) -> None: # Delete after Kurt sees this
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

    def render_old(self, surf:pygame.Surface) -> None: # Delete after Kurt sees this
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
        """Return pixel-space point 'p' in world-space coordinates."""
        return (round(p[0]/self.game.tile_size), round(p[1]/self.game.tile_size))

    def gp(self, p:tuple) -> tuple:
        """Return world-space point 'p' in pixel-space coordinates."""
        return (p[0]*self.game.tile_size, p[1]*self.game.tile_size)

class LevelMenu:
    def __init__(self, game):
        self.game = game
        self.selected = 0
    def move_up(self) -> None:
        self.selected = max(0, self.selected-1)
        # logger.debug(self.selected)
    def move_down(self) -> None:
        num_levels = len(self.game.level_names)
        self.selected = min(num_levels-1, self.selected+1)
        # logger.debug(self.selected)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.save_file = "level.json"  # To pretty print "level.json": $ python -m json.tool level.json
        self.os_window = pygame.display.set_mode((16*50,9*50), flags=pygame.RESIZABLE)
        pygame.display.set_caption("Collisions")
        os.environ["PYGAME_BLEND_ALPHA_SDL2"] = "1"     # Use SDL2 alpha blending
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.xfm = Xfm(self)
        self.tile_size = 50
        self.tile_map = TileMap(self)
        self.player = Player(self)
        self.debug = True
        self.state = 'play' # 'play', 'choose level'
        self.level_menu = LevelMenu(self)

    def run(self):
        while True: self.game_loop()

    def KEYDOWN(self, event):
        kmod = pygame.key.get_mods()
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_F2:
                self.debug = not self.debug
        match self.state:
            case 'choose level':
                match event.key:
                    case pygame.K_UP:       self.level_menu.move_up()
                    case pygame.K_DOWN:     self.level_menu.move_down()
                    case pygame.K_RETURN:   self.load()
            case _:
                match event.key:
                    case pygame.K_LEFT:     self.player.move_left()
                    case pygame.K_RIGHT:    self.player.move_right()
                    case pygame.K_UP:       self.player.move_up()
                    case pygame.K_DOWN:     self.player.move_down()
                    case pygame.K_a:        self.player.move_left()
                    case pygame.K_d:        self.player.move_right()
                    case pygame.K_w:        self.player.move_up()
                    case pygame.K_s:
                        if (kmod & pygame.KMOD_CTRL): self.save()
                        else:               self.player.move_down()
                    case pygame.K_l:
                        if (kmod & pygame.KMOD_CTRL): self.open_load_menu()

    def save(self) -> None:
        logger.debug(f"Saved tile map to \"{self.save_file}\"")
        with open(self.save_file, 'w') as fp:
            json.dump(self.tile_map.tiles, fp, sort_keys=False, indent=4)

    def open_load_menu(self) -> None:
        """Enter 'choose level' state. Create a list of levels in self.level_names."""
        logger.debug("Load file")
        self.state = 'choose level'

        # Load a list of level names
        levels_dir = Path("levels")
        level_files = os.listdir(levels_dir)
        self.level_names = []
        for name in level_files:
            if name.startswith("level") and name.endswith("json"):
                self.level_names.append(name)

    def load(self) -> None:
        """Load the selected level."""
        logger.debug(f"Load {self.level_names[self.level_menu.selected]}")
        # LEFT OFF HERE: load the selected level into self.tile_map.tiles

    def game_loop(self):
        self.handle_events()
        self.text_hud = TextHud(self, size=20) if self.debug else None
        self.player_update()
        self.render()
        self.clock.tick(60)
        self.dt = self.clock.get_time()

    def render(self):
        # Erase window
        self.os_window.fill(Color(30,30,30))

        # Draw the player
        pygame.draw.polygon(self.os_window, Color(255,0,0), self.player.art)

        # Overlay a white outline showing player's collision box
        if self.debug: pygame.draw.rect(self.os_window, Color(255,255,255), self.player.debug_rect, width=1)

        # Draw the tile map
        self.tile_map.render(self.os_window)

        # Draw other things depending on the game state
        match self.state:
            case 'choose level': self.render_level_menu()
            case _: pass

        # Overlay the debug HUD
        if self.debug: self.text_hud.render(self.os_window, Color(255,255,255))

        # Send final video frame to display
        pygame.display.update()

    def render_level_menu(self) -> None:
        win_size = self.os_window.get_size()
        # Grey out the game
        grey_surf = pygame.Surface(win_size, flags=pygame.SRCALPHA)
        grey_surf.fill(Color(255,255,255,100))
        ### blit(source, dest, area=None, special_flags=0) -> Rect
        self.os_window.blit(grey_surf, (0,0), special_flags=pygame.BLEND_ALPHA_SDL2)
        # Center menu in OS window
        menu_size = (300,400)
        menu_rect = Rect(((win_size[0]-menu_size[0])/2,(win_size[1]-menu_size[1])/2), menu_size)
        pygame.draw.rect(self.os_window, Color(30,30,30), menu_rect)
        pygame.draw.rect(self.os_window, Color(255,255,255), menu_rect, width=5)
        # Draw the level names: show which level is selected
        selected   = {'size':40, 'color':Color(255,255,0)}; # Large yellow text
        unselected = {'size':30, 'color':Color(255,255,255)}; # Normal white text
        _text = Text(size=selected['size']) # Dummy Text instance to get _text.linesize for vertical spacing
        for i,level in enumerate(self.level_names):
            text_level = Text(size=selected['size']) if i==self.level_menu.selected else Text(size=unselected['size'])
            text_level.msg = level.strip(".json")
            text_level.pos = (text_level.center_x(menu_rect), menu_rect.top + (1+i*2)*_text.linesize)
            color = selected['color'] if i==self.level_menu.selected else unselected['color']
            text_level.render(self.os_window, color)

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
