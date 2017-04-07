# reference:
# https://github.com/jbradberry/boardgame-socketserver
# http://code.activestate.com/recipes/408859-socketrecv-three-ways-to-turn-it-into-recvall/

import json
import random
import sys
import reversi
import struct
import argparse
import thread

import gevent, gevent.local, gevent.queue, gevent.server


class Server(object):
    def __init__(self, board, addr=None, port=None, use_gui = False):
        self.board = board
        self.states = []  # @ST @NOTE it stores the whole history of the game, but actually we are only insterested in self.states[-1]
        self.local = gevent.local.local()
        self.server = None
        # player message queues
        self.players = dict((x, gevent.queue.Queue())
                            for x in xrange(1, self.board.num_players+1))
        # random player selection @ST ??? for what
        self.player_numbers = gevent.queue.JoinableQueue()

        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242

        self.use_gui = use_gui

    def game_reset(self):
        while True:
            # initialize the game state
            del self.states[:]  # @ST so elegant
            state = self.board.starting_state()
            self.states.append(state)

            # update all players with the starting state
            state = self.board.unpack_state(state)
            # board = self.board.get_description()
            for x in xrange(1, self.board.num_players+1):
                self.players[x].put_nowait({
                    'type': 'update',
                    'board': None,  # board,
                    'state': state,
                })

            # randomize the player selection
            players = range(1, self.board.num_players+1)
            # random.shuffle(players)  # @ST we don't need to shuffle players
            for p in players:
                self.player_numbers.put_nowait(p)

            # block until all players have terminated
            self.player_numbers.join()

    def run(self):
        game = gevent.spawn(self.game_reset)
        self.server = gevent.server.StreamServer((self.addr, self.port),
                                                 self.connection)
        print "Starting server..."
        self.server.serve_forever()

        # FIXME: need a way of nicely shutting down.
        # print "Stopping server..."
        # self.server.stop()

    def connection(self, socket, address):
        print "connection:", socket
        self.local.socket = socket
        if self.player_numbers.empty():
            self.send({
                'type': 'decline', 'message': "Game in progress."
            })
            socket.close()
            return

        self.local.run = True
        self.local.player = self.player_numbers.get()
        self.send({'type': 'player', 'message': self.local.player})

        while self.local.run:
            data = self.players[self.local.player].get()
            try:
                self.send(data)
                if data.get('winners') is not None:
                    self.local.run = False

                elif data.get('state', {}).get('player') == self.local.player:
                    message = self.recv(socket, 4096)
                    messages = message.rstrip().split('\r\n')  # FIXME @ST \r\n is disgusting
                    self.parse(messages[0]) # FIXME: support for multiple messages
                                            #        or out-of-band requests
            except Exception as e:
                print e, 'blabla'
                socket.close()
                self.player_numbers.put_nowait(self.local.player)
                self.players[self.local.player].put_nowait(data)
                self.local.run = False
        self.player_numbers.task_done()

    def parse(self, msg):
        try:
            data = json.loads(msg)
            if data.get('type') != 'action':
                raise Exception
            self.handle_action(data.get('message'))
        except Exception:
            self.players[self.local.player].put({
                'type': 'error', 'message': msg
            })

    def handle_action(self, notation):
        action = self.board.pack_action(notation)
        if not self.board.is_legal(self.states, action):
            self.players[self.local.player].put({
                'type': 'illegal', 'message': notation
            })
            return

        self.states.append(self.board.next_state(self.states[-1], action))
        state = self.board.unpack_state(self.states[-1])

        data = {
            'type': 'update',
            'board': None,
            'state': state,
            'last_action': {
                'player': state['previous_player'],
                'notation': notation,
                'sequence': len(self.states),
            },
        }
        if self.board.is_ended(self.states):
            data['winners'] = self.board.win_values(self.states)
            data['points'] = self.board.points_values(self.states)

        #for x in xrange(1, self.board.num_players+1):
        self.players[3 - self.local.player].put(data)  # @ST send to opponent

    def send(self, data):
        # @ST we need to wrap our communication protocol
        if data['type'] != 'update' or data.get('last_action') is None:
            return
        r, c = self.board.pack_action(data['last_action']['notation'])
        wrapped_data = {'x': c + 1, 'y': r + 1}
        data_json = "{0}\r\n".format(json.dumps(wrapped_data))
        self.local.socket.sendall(struct.pack('>i', len(data_json))+data_json)

    def recv(self, socket, expected_size):
        #data length is packed into 4 bytes
        total_len = 0
        total_data = []
        size=sys.maxint
        size_data = sock_data = ''
        recv_size = expected_size
        while total_len < size:
            sock_data = socket.recv(recv_size)
            if not total_data:
                if len(sock_data) > 4:
                    size_data += sock_data
                    size = struct.unpack('>i', size_data[:4])[0]
                    recv_size = size
                    if recv_size > 524288:
                        recv_size=524288
                    total_data.append(size_data[4:])
                else:
                    size_data += sock_data
            else:
                total_data.append(sock_data)
            total_len=sum([len(i) for i in total_data ])

            # @ST unwrapped message
            message = ''.join(total_data)
            messages = message.rstrip().split('\r\n')  # FIXME @ST \r\n is disgusting
            data = json.loads(messages[0])
            cols = 'abcdefgh'
            if 'x' in data and 'y' in data:
                message = {'message': cols[int(data['x']) - 1] + format(data['y']), 'type': 'action'}
                message = "{0}\r\n".format(json.dumps(message))
        return message

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A server for board game with/without gui")
    parser.add_argument('-g', '--gui', action = 'store_true', dest = 'use_gui', default = False)
    parser.add_argument('address', nargs='?')
    parser.add_argument('port', nargs='?', type=int)

    args = parser.parse_args()

    reversiServer = Server(reversi.Board(), args.address, args.port, args.use_gui)
    reversiServer.run()
