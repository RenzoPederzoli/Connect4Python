import time
from urllib import response
import numpy as np
import pygame
import pygame_menu
import sys
import math
import threading

from comms import Comms

BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

ROW_COUNT = 6
COLUMN_COUNT = 7

SQUARESIZE = 100

width = COLUMN_COUNT * SQUARESIZE
height = (ROW_COUNT+1) * SQUARESIZE

RADIUS = int(SQUARESIZE/2 - 5)

#For communication
comm = Comms()

class SceneBase:
    def __init__(self):
        self.next = self

    def ProcessInput(self, events, pressed_keys):
        print("uh-oh, you didn't override this in the child class")

    def Update(self):
        print("uh-oh, you didn't override this in the child class")

    def Render(self, screen):
        print("uh-oh, you didn't override this in the child class")

    def SwitchToScene(self, next_scene):
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)

# This is to use pygame-menu library correctly
menus = {}
def run_game(width, height, fps, starting_scene):
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    menus["Login"] = pygame_menu.Menu('Login/Signup', width, height, theme=pygame_menu.themes.THEME_BLUE)
    menus["Main"] = pygame_menu.Menu('Main Menu', width, height, theme=pygame_menu.themes.THEME_BLUE)
    menus["Wait"] = pygame_menu.Menu('Waiting', width, height, theme=pygame_menu.themes.THEME_BLUE)

    active_scene = starting_scene()

    while active_scene != None:
        pressed_keys = pygame.key.get_pressed()

        # Event filtering
        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                    pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_ESCAPE:
                    quit_attempt = True
                elif event.key == pygame.K_F4 and alt_pressed:
                    quit_attempt = True

            if quit_attempt:
                active_scene.Terminate()
            else:
                filtered_events.append(event)

        active_scene.ProcessInput(filtered_events, pressed_keys)
        active_scene.Update()
        active_scene.Render(screen)

        active_scene = active_scene.next

        pygame.display.flip()
        clock.tick(fps)


class LoginScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.uname = ""
        self.upass = ""
        menus["Login"].add.text_input('UserName : ', default='jon', onchange=self.uname_control)
        menus["Login"].add.text_input('Password : ', default='123', onchange=self.upass_control)
        menus["Login"].add.button('Submit', self.start_the_game)
        menus["Login"].add.button('Quit', pygame_menu.events.EXIT)

    def ProcessInput(self, events, pressed_keys):
        menus["Login"].update(events)
        for event in events: 
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Move to the next scene when the user pressed Enter for quick tests
                self.SwitchToScene(GameScene())

    def Update(self):
        pass

    def Render(self, screen):
        menus["Login"].draw(screen)

    def start_the_game(self):
        response = comm.signup(self.uname, self.upass)
        if (response.status_code == 200):
            self.SwitchToScene(MainScene())
        else:
            print(response.json())

    def uname_control(self, text):
        self.uname = text

    def upass_control(self, text):
        self.upass = text

class MainScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        menus["Main"].add.label('Welcome '+comm._auth['USERNAME'], font_size=48)
        menus["Main"].add.button('Play', self.start_the_game)
        menus["Main"].add.button('Quit', pygame_menu.events.EXIT)

    def ProcessInput(self, events, pressed_keys):
        menus["Main"].update(events)

    def Update(self):
        pass

    def Render(self, screen):
        menus["Main"].draw(screen)

    def start_the_game(self):
        response = comm.startgame()
        if (response.status_code == 200):
            if comm._game_obj['STATUS'] == "STARTED":
                self.SwitchToScene(GameScene())
            else:
                self.SwitchToScene(WaitingScene())
        else:
            print(response.json())

class WaitingScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        menus["Wait"].add.label('Finding Match ... ', font_size=48)
        t1 = threading.Thread(target=self.ping_server)
        t1.start()

    def ProcessInput(self, events, pressed_keys):
        menus["Wait"].update(events)

    def Update(self):
        pass

    def Render(self, screen):
        menus["Wait"].draw(screen)

    #Threaded function to check for game
    def ping_server(self):
        time_limit = 600 #10 min ping limit
        check_interval = 1 #check every second
        now = time.time()
        last_time = now + time_limit
        while (time.time() <= last_time):
            if (self.check_for_game()):
                break
            else:
                time.sleep(check_interval)

    def check_for_game(self):
        response = comm.getgame()
        if (response.status_code == 200):
            if (comm._game_obj['STATUS'] == "STARTED"):
                self.SwitchToScene(GameScene())
                return True
            else:
                return False
        else:
            print(response.json())
            return False

class GameScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.board = np.transpose(comm._game_obj["BOARD"]) # had to deal with weird board from server...
        self.custom_events = []
        self.count = 0

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()

            # Cant draw in ProcessInput, added to custom events processed in Render
            if event.type == pygame.MOUSEMOTION:
                self.custom_events.append(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.custom_events.append(event)
                posx = event.pos[0]
                col = int(math.floor(posx/SQUARESIZE))

                if comm._game_obj['PLAYERS'][comm._game_obj['TURN']] == comm._auth["USERNAME"]:
                    self.make_move(col)

    def Update(self):
        #Quick way to check every 60 seconds
        if (self.count == 60):
            if (comm._game_obj['PLAYERS'][comm._game_obj['TURN']] != comm._auth["USERNAME"]):
                self.check_for_turn()
            self.count = 0
        self.count += 1

    def Render(self, screen):
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT):
                pygame.draw.rect(
                    screen, BLUE, (c*SQUARESIZE, r*SQUARESIZE+SQUARESIZE, SQUARESIZE, SQUARESIZE))
                pygame.draw.circle(screen, BLACK, (int(
                    c*SQUARESIZE+SQUARESIZE/2), int(r*SQUARESIZE+SQUARESIZE+SQUARESIZE/2)), RADIUS)

        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT):
                if self.board[r][c] == 1:
                    pygame.draw.circle(screen, RED, (int(
                        c*SQUARESIZE+SQUARESIZE/2), height-int((ROW_COUNT - r - 1)*SQUARESIZE+SQUARESIZE/2)), RADIUS)
                elif self.board[r][c] == 2: #(ROW_COUNT - r - 1) had to do this cause of transpose
                    pygame.draw.circle(screen, YELLOW, (int(
                        c*SQUARESIZE+SQUARESIZE/2), height-int((ROW_COUNT - r - 1)*SQUARESIZE+SQUARESIZE/2)), RADIUS)

        for event in self.custom_events:
            if event.type == pygame.MOUSEMOTION:
                pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE))
                posx = event.pos[0]
                if (comm._game_obj["PLAYERS"][0] == comm._auth["USERNAME"]):
                    pygame.draw.circle(screen, RED, (posx, int(SQUARESIZE/2)), RADIUS)
                else:
                    pygame.draw.circle(screen, YELLOW, (posx, int(SQUARESIZE/2)), RADIUS)
            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE))

        if comm._game_obj['PLAYERS'][comm._game_obj['TURN']] == comm._auth["USERNAME"]:
            pygame.draw.circle(screen, GREEN, (0+int(SQUARESIZE/16), 0+int(SQUARESIZE/16)), int(RADIUS/8))
        else:
            pygame.draw.circle(screen, RED, (0+int(SQUARESIZE/16), 0+int(SQUARESIZE/16)), int(RADIUS/8))

        # purge custom events
        self.custom_events = []

    def check_for_turn(self):
        response = comm.getgame()
        if (response.status_code == 200):
            self.board = np.transpose(comm._game_obj["BOARD"])
            if comm._game_obj['PLAYERS'][comm._game_obj['TURN']] == comm._auth["USERNAME"]:
                return True
            else:
                return False
        else:
            print(response.json())
            return False

    def make_move(self, move):
        response = comm.movegame(move)
        if (response.status_code == 200):
            self.board = np.transpose(comm._game_obj["BOARD"])
            return True
        else:
            return False

if (__name__ == "__main__"):
    run_game(width, height, 60, LoginScene)
