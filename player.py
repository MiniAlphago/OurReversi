# reference:
# https://github.com/jbradberry/boardgame-socketplayer
# http://code.activestate.com/recipes/408859-socketrecv-three-ways-to-turn-it-into-recvall/
import json
import socket
import sys
import reversi
import ai
import argparse
import struct


class Client(object):
    def __init__(self, player, addr=None, port=None):
        self.player = player
        self.running = False
        self.receiver = {'player': self.handle_player,
                         'decline': self.handle_decline,
                         'error': self.handle_error,
                         'illegal': self.handle_illegal,
                         'update': self.handle_update}

        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242

    def run(self):
        self.socket = socket.create_connection((self.addr, self.port))
        self.running = True
        while self.running:
            raw_message = self.recv(4096)
            messages = raw_message.rstrip().split('\r\n')
            for message in messages:
                data = json.loads(message)
                if data['type'] not in self.receiver:
                    raise ValueError(
                        "Unexpected message from server: {0!r}".format(message))

                self.receiver[data['type']](data)

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
        if data.get('winners') is not None:
            print self.player.winner_message(data['winners'])
            self.running = False
        elif data['state']['player'] == self.player.player:
            action = self.player.get_action()
            self.send({'type': 'action', 'message': action})

    def send(self, data):
        data_json = "{0}\r\n".format(json.dumps(data))
        self.socket.sendall(struct.pack('>i', len(data_json))+data_json)

    def recv(self, recv_size):
        #data length is packed into 4 bytes
        total_len = 0
        total_data = []
        size=sys.maxint
        size_data = sock_data = ''
        while total_len < size:
            sock_data = self.socket.recv(recv_size)
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
        return ''.join(total_data)

class HumanPlayer(object):
    def __init__(self, board):
        self.board = board
        self.player = None
        self.history = []

    def update(self, state):
        self.history.append(self.board.pack_state(state))

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    def winner_message(self, winners):
        return self.board.winner_message(winners)

    def get_action(self):
        while True:
            print(u"Please enter your action {0}: ".format(self.board.unicode_pieces[self.player]))
            notation = raw_input()
            #notation = raw_input("Please enter your action: ")
            action = self.board.pack_action(notation)
            if action is None:
                continue
            if self.board.is_legal(self.history, action):
                break
        return notation

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Play a boardgame using a specified player type.")
    parser.add_argument('player')
    parser.add_argument('address', nargs='?')
    parser.add_argument('port', nargs='?', type=int)
    parser.add_argument('-e', '--extra', action='append')

    args = parser.parse_args()

    board = reversi.Board
    player_dict = {'human': HumanPlayer, 'mcts': ai.UCTWins}   #
    player_obj = player_dict[args.player]
    player_kwargs = dict(arg.split('=') for arg in args.extra or ())

    client = Client(player_obj(board(), **player_kwargs),
                           args.address, args.port)
    client.run()
