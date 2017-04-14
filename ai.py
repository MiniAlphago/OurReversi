# reference:
# https://github.com/jbradberry/mcts

from __future__ import division

import time
from math import log, sqrt
from random import choice
import threading
import pygame
import widget
import abc

def threaded(fn):  # @ST to wrap a thread function
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

players_name = ['White', 'Black']  # @ST these names will be shown on GUI

class AI(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.history = []

        # @NOTE for multithreading
        self.state_mutex = threading.Lock()
        self.status_text =''
        self.status_text_mutex = threading.Lock()

    def update(self, state):
        self.history.append(self.board.pack_state(state))

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    def winner_message(self, winners):
        return self.board.winner_message(winners)

    @abc.abstractmethod
    def get_action(self):
        """ get action method """
        return

    @threaded
    def show_gui(self):
        FPS = 60
        clock = pygame.time.Clock()
        window     = widget.Window(1400, 800, 'Welcome to Reversi AI', 'resources/images/background_100x100.png')
        keyboard   = widget.Keyboard()
        board_widget      = widget.Board(window, 2, [0], players_name, 8, 8, 1, ('resources/images/white_82x82.png',         \
                          'resources/images/black_82x82.png', 'resources/images/board_82x82_b1.png'),                \
                          'resources/images/cursor_82x82.png')
        scoreboard = widget.ScoreBoard(window, 2, board_widget, ('resources/images/white_82x82.png',                               \
                                'resources/images/black_82x82.png', 'resources/images/background_100x100.png'))

        while True:
            # @ST if ESC is pressed, close window
            if not keyboard.monitor():
                window.quit()
                return

            self.state_mutex.acquire()  # @ST self.history is shared among threads, we need a lock here
            if len(self.history) > 0:
                state = self.history[-1]
                self.state_mutex.release()
            else:
                self.state_mutex.release()
                continue
            pieces = [[-1]*self.board.cols for _ in range(self.board.rows)]  # @ST @NOTE we use -1 for empty, 0 for player 1 and 1 for player 2
            score = [0, 0]  # @ST count pieces for two players
            p1_placed, p2_placed, previous, player = state
            for r in xrange(self.board.rows):
                for c in xrange(self.board.cols):
                    index = 1 << (self.board.cols * r + c)
                    if index & p1_placed:
                        pieces[r][c] = 0
                        score[0] += 1
                    if index & p2_placed:
                        pieces[r][c] = 1
                        score[1] += 1
            score[0] = format(score[0])
            score[1] = format(score[1])
            window.draw_background()
            board_widget.draw_self(pieces)
            self.status_text_mutex.acquire()  # @ST again, shared variable
            scoreboard.draw_self(score, self.status_text) # @ST display info about who's turn or who's the winner,
            self.status_text_mutex.release()
            window.update()  # @ST @NOTE You must call window.update() after you have drawn everything needed, or the screnn will flicker and flicker...
            clock.tick(FPS)
