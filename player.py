# reference:
# https://github.com/jbradberry/boardgame-socketplayer
# http://code.activestate.com/recipes/408859-socketrecv-three-ways-to-turn-it-into-recvall/
# https://github.com/merryChris/reversi

import json
import socket
import sys
import reversi
import ai
import ai2
import argparse
import struct
import threading
import time
import widget
import pygame

def threaded(fn):  # @ST to wrap a thread function
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

players_name = ['White', 'Black']  # @ST these names will be shown on GUI

class Client(object):
    def __init__(self, player, addr=None, port=None, use_gui = False):
        self.player = player
        self.running = False
        self.receiver = {'player': self.handle_player,
                         'decline': self.handle_decline,
                         'error': self.handle_error,
                         'illegal': self.handle_illegal,
                         'update': self.handle_update}

        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242
        self.use_gui = use_gui
        self.player.use_gui = use_gui  # @ST we need use_gui in get_action()


    def run(self):
        self.socket = socket.create_connection((self.addr, self.port))
        self.running = True

        # @ST we need to determine who to put a piece first
        print(u"Which player do you want to be, 1 {0} or 2 {1}?".format(self.player.board.unicode_pieces[1], self.player.board.unicode_pieces[2]))
        player = raw_input()
        print "You are player #{0}.".format(player)
        self.player.player = int(player)   # @ST 1 or 2

        # @ST create the show gui thread
        if self.use_gui:
            show_gui_thread = self.player.show_gui()

        # @ST update the player with the starting state
        state = self.player.board.starting_state()
        state = self.player.board.unpack_state(state)
        self.handle_update({'state': state})

        #if self.player.player == 1:
        #    self.handle_my_turn()

        while self.running:
            raw_message = self.socket.recv(4096)
            messages = raw_message.rstrip().split('\r\n')
            if self.use_gui:
                self.player.status_text_mutex.acquire()
                self.player.status_text = '{0}\'s Turn'.format(players_name[self.player.player - 1])
                self.player.status_text_mutex.release()

            for message in messages:
                try:
                    data = json.loads(message)
                    #if data['type'] not in self.receiver:
                    #    raise ValueError(
                    #        "Unexpected message from server: {0!r}".format(message))
                except ValueError:  # @ST in case we receive two or more messages
                        raise ValueError("Unexpected message from server: {0!r}".format(message))
                self.handle_opponent_action(data)

        # @ST game over
        if self.use_gui:
            try:
                while True:
                    continue  # @ST do nothing, just waiting to exit
            except KeyboardInterrupt:
                pass
            # join gui thread
            show_gui_thread.join()

    def handle_player(self, data):
        player = data['message']
        print "You are player #{0}.".format(player)
        self.player.player = player

    def handle_decline(self, data):
        print data['message']
        self.running = False

    def handle_error(self, data):
        print data['message'] # FIXME: do something useful

    def handle_illegal(self, data):
        print data['message'] # FIXME: do something useful

    def handle_update(self, data):
        state = data['state']
        action = data.get('last_action', {}).get('notation') or ''
        self.player.update(state)

        print self.player.display(state, action)
        if self.use_gui:
            self.player.status_text_mutex.acquire()
            self.player.status_text = '{0}\'s Turn'.format(players_name[data['state']['player'] - 1])
            self.player.status_text_mutex.release()

        if data.get('winners') is not None:
            print self.player.winner_message(data['winners'])
            if self.use_gui:
                self.player.status_text_mutex.acquire()
                self.player.status_text = self.player.winner_message(data['winners'])
                self.player.status_text_mutex.release()
            self.running = False
        elif data['state']['player'] == self.player.player:
            self.handle_my_turn()
            #action = self.player.get_action()
            #self.send({'type': 'action', 'message': action})

    def send(self, data):
        # @ST wrap message
        if not data['message']:
            r, c = -1, -1
        else:
            r, c = self.player.board.pack_action(data['message'])
            r = r + 1
            c = c + 1
        wrapped_data = {'x': c, 'y': r}
        data_json = "{0}\r\n".format(json.dumps(wrapped_data))
        #print(data_json)  # @DEBUG
        self.socket.sendall(data_json)

    def recv(self, expected_size):
        #data length is packed into 4 bytes
        total_len = 0
        total_data = []
        size=sys.maxint
        size_data = sock_data = ''
        recv_size = expected_size
        while total_len < size:
            sock_data = self.socket.recv(recv_size)
            if not total_data:
                if len(sock_data) > 4:
                    size_data += sock_data
                    size = struct.unpack('>i', size_data[:4])[0]
                    recv_size = size
                    if recv_size > 524288:
                        recv_size = 524288
                    total_data.append(size_data[4:])
                else:
                    size_data += sock_data
            else:
                total_data.append(sock_data)
            total_len=sum([len(i) for i in total_data ])

        return ''.join(total_data)

    def handle_opponent_action(self, data):
        # @ST unwrapped message
        #print(data)  # @DEBUG
        action = (int(data['y']) - 1, int(data['x']) - 1)  # @ST [row, col]
        #print(action)  # @DEBUG
        if action[0] < 0 or action[1] < 0:  # @ST your opponent did not put a piece
            # @ST it's our turn to put a piece again

            #self.player.state_mutex.acquire()
            #state = self.player.history[-1]
            #new_state = (state[0], state[1], state[3], state[2])
            #self.player.history.append(new_state)
            #self.player.state_mutex.release()

            self.handle_my_turn()
            return

        self.player.state_mutex.acquire()
        if not self.player.board.is_legal(self.player.history, action):  # @ST @NOTE here we assume that we do not preempt
            # @ST maybe we have to wait again
            invalid_msg = '{0}: invalid move at row {1}, column {2}'.format(players_name[data['state']['player'] - 1], action[0] + 1, action[1] + 1)
            print(invalid_msg)
            if self.use_gui:
                self.player.status_text_mutex.acquire()
                self.player.status_text = invalid_msg
                self.player.status_text_mutex.release()
            self.player.state_mutex.release()
            return
        self.player.state_mutex.release()

        self.player.state_mutex.acquire()
        state = self.player.board.next_state(self.player.history[-1], action)
        self.player.update(self.player.board.unpack_state(state))  # @ST put a piece and flip
        history_copy = self.player.history[:]
        self.player.state_mutex.release()

        print self.player.display(self.player.board.unpack_state(state), self.player.board.unpack_action(action))

        if self.player.board.is_ended(history_copy):

            win_msg = self.player.board.winner_message(self.player.board.win_values(history_copy))
            print(win_msg)

            if self.use_gui:
                self.player.status_text_mutex.acquire()
                self.player.status_text = win_msg
                self.player.status_text_mutex.release()
            self.running = False
            return

        # OK, my turn
        if state[3] == self.player.player:
            self.handle_my_turn()
        else:
            #print(['*'] * 100)  # @DEBUG
            self.send({'type': 'action', 'message': None})


    def handle_my_turn(self):
        action = self.player.get_action()
        message = {'type': 'action', 'message': action}

        #print(action, action == None)
        #if action == None:  # @ST we just do nothing
        #    print(['*'] * 1000) # @DEBUG
        #    self.player.state_mutex.acquire()
        #    state = self.player.history[-1]
        #    new_state = (state[0], state[1], state[3], state[2])
        #    self.player.history.append(new_state)
        #    self.player.state_mutex.release()
        #    return

        action = self.player.board.pack_action(action)
        self.player.state_mutex.acquire()
        state = self.player.board.next_state(self.player.history[-1], action)
        self.player.update(self.player.board.unpack_state(state))  # @ST put a piece and flip
        history_copy = self.player.history[:]
        self.player.state_mutex.release()
        print self.player.display(self.player.board.unpack_state(state), self.player.board.unpack_action(action))

        self.send(message)

        if self.use_gui:
            self.player.status_text_mutex.acquire()
            self.player.status_text = '{0}\'s Turn'.format(players_name[2 - self.player.player])
            self.player.status_text_mutex.release()

        if self.player.board.is_ended(history_copy):
            win_msg = self.player.board.winner_message(self.player.board.win_values(history_copy))
            print(win_msg)

            if self.use_gui:
                self.player.status_text_mutex.acquire()
                self.player.status_text = win_msg
                self.player.status_text_mutex.release()
            self.running = False
            return

class HumanPlayer(object):

    def __init__(self, board):
        self.board = board
        self.player = None
        self.history = []
        self.coordinate = None


        # @NOTE for multithreading
        self.state_mutex = threading.Lock()
        self.status_text =''
        self.status_text_mutex = threading.Lock()

        #@CH condition variable
        self.condition = threading.Condition()

        self.gui_is_on = False
        self.gui_is_on_mutex = threading.Lock()


    def update(self, state):
        self.history.append(self.board.pack_state(state))

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    @threaded
    def show_gui(self):
        FPS = 60
        clock = pygame.time.Clock()
        window     = widget.Window(1400, 800, 'Welcome to Reversi AI', 'resources/images/background_100x100.png')
        keyboard   = widget.Keyboard()
        board_widget = widget.Board(window, 2, [0], players_name, 8, 8, 1, ('resources/images/white_82x82.png',         \
                          'resources/images/black_82x82.png', 'resources/images/board_82x82_b1.png'),                \
                          'resources/images/cursor_82x82.png')
        scoreboard = widget.ScoreBoard(window, 2, board_widget, ('resources/images/white_82x82.png',                               \
                                'resources/images/black_82x82.png', 'resources/images/background_100x100.png'))

        self.gui_is_on_mutex.acquire()
        self.gui_is_on = True
        self.gui_is_on_mutex.release()

        while True:
            if not keyboard.monitor(onkeydown_callback=board_widget.update):
                self.gui_is_on_mutex.acquire()
                self.gui_is_on = False
                self.gui_is_on_mutex.release()

                self.condition.acquire()
                self.condition.notify()  # gui is off
                self.condition.release()
                print('Closing window...')
                window.quit()
                return

            self.condition.acquire()
            location = board_widget.get_location()
            if location is not None:

                self.coordinate = location
                #print 'show_gui set self.coordinate as: ', self.coordinate  # @DEBUG
                self.condition.notify()
            self.condition.release()

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
            board_widget.draw_self(pieces, True)
            self.status_text_mutex.acquire()  # @ST again, shared variable
            scoreboard.draw_self(score, self.status_text) # @ST display info about who's turn or who's the winner,
            self.status_text_mutex.release()
            window.update()  # @ST @NOTE You must call window.update() after you have drawn everything needed, or the screnn will flicker and flicker...
            clock.tick(FPS)

        while True:
            # @ST if ESC is pressed, close window
            if not keyboard.monitor():
                window.quit()
                return

    def winner_message(self, winners):
        return self.board.winner_message(winners)

    def get_action(self):
        self.state_mutex.acquire()
        if not self.board.legal_actions(self.history):  # @ST return early if there is no legal move
            self.state_mutex.release()
            return
        self.state_mutex.release()

        while True:
            if self.use_gui:
                self.condition.acquire()
                if not self.coordinate:
                    #print ("go to sleep ...")  # @DEBUG
                    self.condition.wait()
                #print ("waken up...", self.coordinate)  # @DEBUG
                pressed_coordinate = self.coordinate
                self.condition.release()

                self.gui_is_on_mutex.acquire()
                if self.gui_is_on:
                    notation = str(chr(pressed_coordinate[1]+97))+str(pressed_coordinate[0]+1)
                    self.coordinate = None
                else:  # @ST unfortunately the gui is closed by user
                    print(u"Please enter your action {0}: ".format(self.board.unicode_pieces[self.player]))
                    notation = raw_input()
                self.gui_is_on_mutex.release()

            else:
                print(u"Please enter your action {0}: ".format(self.board.unicode_pieces[self.player]))
                notation = raw_input()

            action = self.board.pack_action(notation)
            if action is None:
                continue

            self.state_mutex.acquire()
            if self.board.is_legal(self.history, action):
                self.state_mutex.release()
                break
            self.state_mutex.release()
        return notation

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Play a boardgame using a specified player type.")
    parser.add_argument('-g', '--gui', action = 'store_true', dest = 'use_gui', default = False)
    parser.add_argument('player')
    parser.add_argument('address', nargs='?')
    parser.add_argument('port', nargs='?', type=int)
    parser.add_argument('-e', '--extra', action='append')

    args = parser.parse_args()

    board = reversi.Board
    player_dict = {'human': HumanPlayer, 'mcts': ai.UCTWins,'mcts2':ai2.UCTWins}   # @TODO we need to use our own AIs
    player_obj = player_dict[args.player]
    player_kwargs = dict(arg.split('=') for arg in args.extra or ())

    client = Client(player_obj(board(), **player_kwargs),
                           args.address, args.port, args.use_gui)
    client.run()
