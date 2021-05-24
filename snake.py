import pygame
import sys
import random
from structures import *

TICK_RATE = 10

BAR_HEIGHT = 40
SCREEN_HEIGHT = 1000
BOARD_SIZE = 40
SCREEN_WIDTH = SCREEN_HEIGHT - BAR_HEIGHT
TILE_SIZE = SCREEN_WIDTH / BOARD_SIZE

BG_COLOR = (0, 0, 0)
SNAKE_COLOR = (0, 255, 0)
FOOD_COLOR = (255, 0, 0)

UP = Position(0, -1)
DOWN = Position(0, 1)
LEFT = Position(-1, 0)
RIGHT = Position(1, 0)


class Food:
    def __init__(self):
        self.position = None
        self.randomize_position()

    def randomize_position(self):
        x = random.randrange(1, BOARD_SIZE - 1)
        y = random.randrange(1, BOARD_SIZE - 1)
        self.position = Position(x, y)

    def draw(self, surface):
        r = pygame.Rect((self.position * TILE_SIZE).as_tuple(), (TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surface, FOOD_COLOR, r)
        pygame.draw.rect(surface, BG_COLOR, r, 1)


class Snake:
    def __init__(self):
        self.direction = RIGHT
        middle = Position(BOARD_SIZE / 2, BOARD_SIZE / 2)
        self.positions = Queue()
        self.positions.push(middle + 2 * LEFT)
        self.positions.push(middle + LEFT)
        self.positions.push(middle)

    def reset(self):
        self.__init__()

    def get_head_position(self):
        return self.positions.peek(index=self.positions.len() - 1)

    def turn(self, dir):
        if self.direction != (-1 * dir):  # Can't turn backwards
            self.direction = dir

    def move(self):
        self.positions.push(self.get_head_position() + self.direction)
        self.positions.pop()

    def increase_length(self):
        tail = self.positions.peek()
        next = self.positions.peek(1)
        dir = tail - next
        self.positions.insert(0, tail + dir)

    def draw(self, surface):
        for position in self.positions.queue:
            r = pygame.Rect((position * TILE_SIZE).as_tuple(), (TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, SNAKE_COLOR, r)
            pygame.draw.rect(surface, BG_COLOR, r, 1)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 16)

        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.best = 0

    def play(self):
        while True:
            self.tick()
            self.handle_inputs()
            self.render()

    def handle_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.turn(UP)
                elif event.key == pygame.K_DOWN:
                    self.snake.turn(DOWN)
                elif event.key == pygame.K_LEFT:
                    self.snake.turn(LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.snake.turn(RIGHT)

    def tick(self):
        self.snake.move()
        if self.food.position in self.snake.positions.queue:
            self.snake.increase_length()
            self.score += 1
            if self.score > self.best:
                self.best = self.score
            self.food.randomize_position()
        elif self.snake.get_head_position() in self.snake.positions.queue[:-1]:
            self.snake.reset()
            self.score = 0
        elif not ((0 <= self.snake.get_head_position().x < BOARD_SIZE) and (
                0 <= self.snake.get_head_position().y < BOARD_SIZE)):
            self.snake.reset()
            self.score = 0
        pygame.display.update()
        self.clock.tick(TICK_RATE)

    def render(self):
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - BAR_HEIGHT))
        scoreArea = pygame.Surface((SCREEN_WIDTH, BAR_HEIGHT))
        surface = surface.convert()
        self.snake.draw(surface)
        self.food.draw(surface)
        pygame.draw.rect(surface, SNAKE_COLOR, surface.get_rect(), 1)
        text = self.font.render(f"Score: {self.score}", True, SNAKE_COLOR)
        text2 = self.font.render(f"Best:  {self.best}", True, SNAKE_COLOR)
        scoreArea.blit(text, (0, 0))
        scoreArea.blit(text2, (SCREEN_WIDTH - 100, 0))
        self.screen.blit(scoreArea, (0, 0))
        self.screen.blit(surface, (0, BAR_HEIGHT))


if __name__ == '__main__':
    game = Game()
    game.play()
