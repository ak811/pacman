import os
import pygame
import pygame.draw
from pygame import Surface
from math import sqrt
from random import randint, shuffle
from time import sleep
from typing import Dict, List, Set, Tuple
import Colors


class Action:
    counter = 0

    def __init__(self) -> None:
        self.index = Action.counter
        Action.counter += 1

    def __hash__(self) -> int:
        return self.index


class Perception:
    def __init__(self, position: Tuple[int, int], isWall: bool) -> None:
        self.position = position
        self.isWall = isWall


class Environment:
    def __init__(self,
                 width: int,
                 height: int,
                 walls: Set[Tuple[int, int]],
                 start: Tuple[int, int],
                 finish: Tuple[int, int]) -> None:
        self.width = width
        self.height = height
        self.walls = walls
        self.start = start
        self.finish = finish

    def perceive(self, position: Tuple[int, int], action: Action) -> Perception:

        x, y = position

        if action is goRight:
            x += 1
        elif action is goUp:
            y -= 1
        elif action is goLeft:
            x -= 1
        elif action is goDown:
            y += 1
        else:
            print("undefined action:", action)

        position = x, y

        return Perception(position, position in self.walls)


def read_maps(file_name: str) -> Environment:
    w: int
    h: int
    walls: Set[Tuple[int, int]]
    spawn: Set[Tuple[int, int]]
    start: Tuple[int, int]
    finish: Tuple[int, int]

    with open(file_name) as f:
        w = 0
        y = 0
        walls = set()
        spawn = set()
        for line in f:

            # remove \n in file
            line = line[None:-1]

            w = max(w, len(line))
            x = 0
            for char in line:
                p = (x, y)
                if char == " ":
                    pass
                elif char == "*":
                    walls.add(p)
                elif char == "#":
                    spawn.add(p)
                else:
                    print("unknown character in map:", char)
                x += 1
            y += 1
        h = y

        start, finish = None, None

        if len(spawn) == 0:
            while start is None or start in walls:
                start = randint(0, w - 1), randint(0, h - 1)
            while finish is None or finish in walls:
                finish = randint(0, w - 1), randint(0, h - 1)
        elif len(spawn) == 1:
            start = spawn.pop()
            while finish is None or finish in walls:
                finish = randint(0, w - 1), randint(0, h - 1)
        else:
            l = list(spawn)
            shuffle(l)
            start, finish = l.pop(), l.pop()

        return Environment(w, h, walls, start, finish)


class Agent:
    def __init__(self, environment: Environment) -> None:
        self.environment = environment
        self.position = environment.start
        self.isTrapped = False
        self.actions = goRight, goUp, goLeft, goDown

        self.visited: Set[Tuple[int, int]]
        self.visited = {self.position}

        self.stack: List[Action]
        self.stack = []

    def act(self) -> None:

        percepts = {a: self.environment.perceive(
            self.position, a) for a in self.actions}

        decision = self.decide(percepts)

        if decision is None:
            self.isTrapped = True
        else:
            self.position = percepts[decision].position

            if self.position not in self.visited:
                self.visited.add(self.position)

    def decide(self, percepts: Dict[Action, Perception]) -> Action:

        def d(a: Action) -> float:
            return distance(percepts[a].position, self.environment.finish)

        decision: Action

        options: List[Action]
        options = [k for k in percepts if not percepts[k].isWall]

        if len(options) == 0:
            decision = None
        else:
            not_perceived = [
                i for i in options if percepts[i].position not in self.visited]
            if len(not_perceived) > 1:
                options = not_perceived
                options.sort(key=d)
                decision = options[0]
            elif len(not_perceived) == 1:
                decision = not_perceived[0]
            else:
                return move(self.stack.pop())

        self.stack.append(decision)
        return decision


def move(action: Action) -> Action:
    if action is goRight:
        return goLeft
    elif action is goUp:
        return goDown
    elif action is goLeft:
        return goRight
    elif action is goDown:
        return goUp
    else:
        print("Undefined action:", action)
        return None


def distance(fr: Tuple[int, int], to: Tuple[int, int]) -> float:
    return sqrt((fr[0] - to[0]) ** 2 + (fr[1] - to[1]) ** 2)


def draw_rect(p: Tuple[int, int]):
    return margin + p[0] * size, margin + p[1] * size


def rect(p: Tuple[int, int]):
    return pygame.Rect(draw_rect(p), (size, size))


def draw_circle(p: Tuple[int, int]):
    return margin + (p[0] + 0.5) * size, margin + (p[1] + 0.5) * size


speed = 15
margin = 0
size = 40
radius = size / 5

goRight = Action()
goUp = Action()
goLeft = Action()
goDown = Action()

root = os.path.dirname(os.path.abspath(__file__))
filename = root + "\\maps\\map2.txt"
environment = read_maps(filename)

agent: Agent
agent = Agent(environment)

pygame.init()
screen: Surface
screen = pygame.display.set_mode(
    (environment.width * size + margin * 2, environment.height * size + margin * 2))

searching = True

while True:

    screen.fill(Colors.gray)

    for x in range(environment.width):
        for y in range(environment.height):
            pair = (x, y)
            if pair in environment.walls:
                color = Colors.dark_blue
            else:
                color = Colors.black

            pygame.draw.rect(screen, color, rect(pair))

    pygame.draw.circle(screen, Colors.white, draw_circle(
        environment.finish), radius)

    for pair in agent.visited:
        pygame.draw.circle(screen, Colors.gray, draw_circle(pair), 3)

    pygame.draw.circle(screen, Colors.yellow,
                       draw_circle(agent.position), radius)

    pygame.display.flip()

    sleep(1 / speed)

    events = pygame.event.get()
    if len(events) > 0:
        for event in events:
            if event.type == pygame.QUIT:
                exit()

    if searching:
        agent.act()
        if agent.position == environment.finish:
            print("The goal has been reached.")
            searching = False
        if agent.isTrapped:
            print("Agent is trapped.")
            searching = False
