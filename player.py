# reference:
# https://github.com/jbradberry/boardgame-socketplayer
# http://code.activestate.com/recipes/408859-socketrecv-three-ways-to-turn-it-into-recvall/
# https://github.com/merryChris/reversi

import json
import socket
import sys
import reversi
import ai
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

players_name = ['Black', 'White']  # @ST these names will be shown on GUI

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

    def run(self):
        self.socket = socket.create_connection((self.addr, self.port))
        self.running = True

        # @ST create the show gui thread
        if self.use_gui:
            show_gui_thread = self.player.show_gui()

        while self.running:
            raw_message = self.recv(4096)
            messages = raw_message.rstrip().split('\r\n')
            for message in messages:
                try:
                    data = json.loads(message)
                    if data['type'] not in self.receiver:
                        raise ValueError(
                            "Unexpected message from server: {0!r}".format(message))
                except ValueError:  # @ST in case we receive two or more messages
                    size = struct.unpack('>i', message[:4])[0]
                    if size == len(message) - 2:
                        data = json.loads(message[4:])
                        if data['type'] not in self.receiver:
                            raise ValueError(
                                "Unexpected message from server: {0!r}".format(message))

                self.receiver[data['type']](data)
        # @ST game over
        try:
            while True:
                continue  # @ST do nothing, just waiting to exit
        except KeyboardInterrupt:
            pass
        # join gui thread
        if self.use_gui:
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
            action = self.player.get_action()
            self.send({'type': 'action', 'message': action})

    def send(self, data):
        data_json = "{0}\r\n".format(json.dumps(data))
        self.socket.sendall(struct.pack('>i', len(data_json))+data_json)

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



    def update(self, state):
        self.state_mutex.acquire()
        self.history.append(self.board.pack_state(state))
        self.state_mutex.release()

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    @threaded
    def show_gui(self):
        FPS = 60
        clock = pygame.time.Clock()
        window     = widget.Window(1200, 800, 'Welcome to Reversi AI', 'resources/images/background_100x100.png')
        keyboard   = widget.Keyboard()
        board_widget = widget.Board(window, 2, [0], players_name, 8, 8, 1, ('resources/images/black_82x82.png',         \
                          'resources/images/white_82x82.png', 'resources/images/board_82x82_b1.png'),                \
                          'resources/images/cursor_82x82.png')
        scoreboard = widget.ScoreBoard(window, 2, board_widget, ('resources/images/black_82x82.png',                               \
                                'resources/images/white_82x82.png', 'resources/images/background_100x100.png'))

        while True:
            if not keyboard.monitor(onkeydown_callback=board_widget.update):
                window.quit()
                return

            self.condition.acquire()
            location = board_widget.get_location()
            if location is not None:

                self.coordinate = location
                print 'show_gui set self.coordinate as: ', self.coordinate
                #print self.coordinate
                #self.condition.wait()
                self.condition.notify()
            #else:
                #print self.coordinate
                #self.condition.notify()
            self.condition.release()
            #time.sleep(1)

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

        while True:
            # @ST if ESC is pressed, close window
            if not keyboard.monitor():
                window.quit()
                return

    def winner_message(self, winners):
        return self.board.winner_message(winners)

    def get_action(self):
        while True:
            print(u"Please enter your action {0}: ".format(self.board.unicode_pieces[self.player]))
            #notation = raw_input()
            self.condition.acquire()
            if not self.coordinate:
                print ("go to sleep ...")
                self.condition.wait()
              #  notation = (5,4)
            #notation = raw_input("Please enter your action: ")
                #self.condition.notify()
            self.condition.release()
            print ("waken up...", self.coordinate)
            notation = str(chr(self.coordinate[1]+97))+str(self.coordinate[0]+1)
            print notation
            self.coordinate = None
            #time.sleep(4)

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
    player_dict = {'human': HumanPlayer, 'mcts': ai.UCTWins}   # @TODO we need to use our own AIs
    player_obj = player_dict[args.player]
    player_kwargs = dict(arg.split('=') for arg in args.extra or ())

    client = Client(player_obj(board(), **player_kwargs),
                           args.address, args.port, args.use_gui)
    client.run()
