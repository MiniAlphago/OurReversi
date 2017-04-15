# reference:
# https://github.com/jbradberry/mcts

from __future__ import division

import time
from math import log, sqrt
from random import choice
import ai
import threading
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Process, Queue

class Stat(object):
    __slots__ = ('value', 'visits')

    def __init__(self, value=0, visits=0):
        self.value = value
        self.visits = visits

class UCT(ai.AI):
    def __init__(self, board, **kwargs):
        super(UCT, self).__init__(board, **kwargs)
        self.stats = {}

        self.max_depth = 0
        self.data = {}
        time = 30    # should be 1 min but in case that time is over
        self.calculation_time = float(time)
        # self.calculation_time = float(kwargs.get('time', 3))  # @ST @NOTE Here calculation_time should be 1 min
        self.max_actions = int(kwargs.get('max_actions', 1000))

        # Exploration constant, increase for more exploratory actions,
        # decrease to prefer actions with known higher win rates.
        self.C = float(kwargs.get('C', 1.96)) #Original1.4

    def get_action(self):

        begin = time.time()
        # Causes the AI to calculate the best action from the
        # current game state and return it.

        self.max_depth = 0
        self.data = {}
        self.stats.clear()

        state = self.history[-1]
        player = self.board.current_player(state)
        legal = self.board.legal_actions(self.history[:])

        # Bail out early if there is no real choice to be made.
        if not legal:
            return
        if len(legal) == 1:
            return self.board.unpack_action(legal[0])

        games = 0
        # @TODO multithreading here
        queue = Queue()
        processes_num = 1
        processes = []
        result = []
        for i in range(processes_num):
            p = Process(target=self.simulation_worker, args = (queue,))
            p.Daemon = True
            p.start()
            processes.append(p)

        for i in range(processes_num):
            result.append(queue.get())

        for i in range(processes_num):
            processes[i].join()

        voting = {}
        for p in legal:
            voting[p] = {'votes': 0, 'wins': 0, 'visits': 0}


        for stats, game_times, max_depth in result:
            # @DEBUG
            print 'games:', game_times
            games += game_times
            self.max_depth = max(self.max_depth, max_depth)

            actions = self.calculate_action_values(state, player, legal, stats)
            highest_score = actions[0]['percent']
            #print actions[0]['wins']
            for action in actions:
                #tmp = voting[action['action']]
                #print tmp, tmp['wins']
                if action['percent'] == highest_score:
                    voting[action['action']]['votes'] += 1
                    voting[action['action']]['wins'] += action['wins']
                    voting[action['action']]['visits'] += action['plays']
                else:
                    break

            # for key in stats.keys():
            #     # @DEBUG
            #     #print stats[key].value, stats[key].visits
            #     S = self.stats.setdefault(key, Stat())
            #     S.value += stats[key].value
            #     S.visits += stats[key].visits
        for key in voting.keys():  # @DEBUG
            if voting[key]['votes'] == 0:
                continue
            print 'action: {0}, votes: {1}, average: {2:.1f}% ({3}/{4})'.format(self.board.unpack_action(key), voting[key]['votes'], 100 * voting[key]['wins'] / voting[key]['visits'], voting[key]['wins'], voting[key]['visits'])

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.data.update(games=games, max_depth=self.max_depth,
                         time=str(time.time() - begin))
        print self.data['games'], self.data['time']
        print "Maximum depth searched:", self.max_depth

        # Store and display the stats for each possible action.
        self.data['actions'] = sorted(
            voting.items(),
            key = lambda x: (x[1]['votes'], x[1]['wins'], x[1]['visits']),
            reverse=True
        )
        # for m in self.data['actions']:
        #     print self.action_template.format(**m)

        # Pick the action with the highest average value.
        return self.board.unpack_action(self.data['actions'][0][0])

    def simulation_worker(self, queue):  # @ST @NOTE here `i` is useless
        games = 0
        begin = time.time()
        stats = {}
        max_depth = 0
        while time.time() - begin < self.calculation_time:
            max_depth = max(self.run_simulation(stats), max_depth)
            games += 1
        queue.put([stats, games, max_depth])
        return


    # Here we run the simulation
    def run_simulation(self, stats):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop. 6

        #stats = {}
        max_depth = 0
        visited_states = set()
        history_copy = self.history[:]
        state = history_copy[-1]
        player = self.board.current_player(state)

        expand = True

        # the most important part
        # Use UCB to evaluate the nodes and
        for t in xrange(1, self.max_actions + 1):
            legal = self.board.legal_actions(history_copy)
            actions_states = [(p, self.board.next_state(state, p)) for p in legal]

            if all((player, S) in stats for p, S in actions_states):
                log_total = log(
                    sum(stats[(player, S)].visits for p, S in actions_states) or 1)
                value, action, state = max(
                    ((stats[(player, S)].value / (stats[(player, S)].visits or 1)) +
                     self.C * sqrt(log_total / (stats[(player, S)].visits or 1)), p, S)
                    for p, S in actions_states
                )
            else:
                # Otherwise, just make an arbitrary decision.
                action, state = choice(actions_states)

            history_copy.append(state)

            # Expand
            # `player` here and below refers to the player
            # who moved into that particular state.
            if expand and (player, state) not in stats:
                expand = False
                stats[(player, state)] = Stat()
                if t > max_depth:
                    max_depth = t

            visited_states.add((player, state))

            player = self.board.current_player(state)
            if self.board.is_ended(history_copy):
                break

        # Back-propagation
        #
        end_values = self.end_values(history_copy)
        for player, state in visited_states:
            if (player, state) not in stats:
                continue
            S = stats[(player, state)]
            S.visits += 1
            S.value += end_values[player]
        return max_depth

class UCTWins(UCT):
    action_template = "{action}: {percent:.2f}% ({wins} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTWins, self).__init__(board, **kwargs)
        self.end_values = board.win_values

    def calculate_action_values(self, state, player, legal, tree):
        actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        return sorted(
            ({'action': p,
              'percent': 100 * tree[(player, S)].value / tree[(player, S)].visits,
              'wins': tree[(player, S)].value,
              'plays': tree[(player, S)].visits}
             for p, S in actions_states),
            key=lambda x: (x['percent'], x['plays']),
            reverse=True
        )


class UCTValues(UCT):
    action_template = "{action}: {average:.1f} ({sum} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTValues, self).__init__(board, **kwargs)
        self.end_values = board.points_values

    def calculate_action_values(self, state, player, legal, tree):
        actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        return sorted(
            ({'action': p,
              'average': tree[(player, S)].value / tree[(player, S)].visits,
              'sum': tree[(player, S)].value,
              'plays': tree[(player, S)].visits}
             for p, S in actions_states),
            key=lambda x: (x['average'], x['plays']),
            reverse=True
        )
