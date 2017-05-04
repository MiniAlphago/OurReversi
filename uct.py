# reference:
# https://github.com/jbradberry/mcts

from __future__ import division

import time
from math import log, sqrt
from random import choice
import ai
import minimax
import reversi

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
        time = 3    # should be 1 min but in case that time is over
        self.calculation_time = float(time)
        # self.calculation_time = float(kwargs.get('time', 3))  # @ST @NOTE Here calculation_time should be 1 min
        self.max_actions = int(kwargs.get('max_actions', 64))

        # Exploration constant, increase for more exploratory actions,
        # decrease to prefer actions with known higher win rates.
        self.C = float(kwargs.get('C', 1.96)) #Original1.4

        self.plugged_in_minimax = minimax.MiniMax(reversi.Board())
        self.minimax_max_depth = 2

    def get_action(self):

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
        begin = time.time()
        while time.time() - begin < self.calculation_time:
            self.run_simulation()
            games += 1

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.data.update(games=games, max_depth=self.max_depth,
                         time=str(time.time() - begin))
        print 'games: {0}, time ellapsed: {1}'.format(self.data['games'], self.data['time'])
        print "Maximum depth searched:", self.max_depth

        # Store and display the stats for each possible action.
        self.data['actions'] = self.calculate_action_values(state, player, legal)
        for m in self.data['actions']:
            print self.action_template.format(**m)

        # Pick the action with the highest average value.
        return self.board.unpack_action(self.data['actions'][0]['action'])

    # Here we run the simulation
    def run_simulation(self):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop. 6
        discs_num = self.board.count_discs(self.history[-1])
        max_searching_depth = self.max_actions - discs_num
        used_minimax_flag = False

        stats = self.stats
        visited_states = set()
        history_copy = self.history[:]
        state = history_copy[-1]
        player = self.board.current_player(state)

        expand = True
        called_minimax = 0

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
                if max_searching_depth <= t * 2:
                    used_minimax_flag = True
                    if player == 1:
                        best_value, best_action = self.plugged_in_minimax.Max(history_copy[-1], self.minimax_max_depth, float('-inf'), float('inf'), player)
                    else:
                        best_value, best_action = self.plugged_in_minimax.Min(history_copy[-1], self.minimax_max_depth, float('-inf'), float('inf'), player)
                    for p, s in actions_states:
                        if p == best_action:
                            action, state = p, s
                # Otherwise, just make an arbitrary decision.
                else:
                    action, state = choice(actions_states)

            history_copy.append(state)

            # Expand
            # `player` here and below refers to the player
            # who moved into that particular state.
            if expand and (player, state) not in stats:
                expand = False
                stats[(player, state)] = Stat()
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, state))

            player = self.board.current_player(state)
            if used_minimax_flag or self.board.is_ended(history_copy):
                if not used_minimax_flag:
                    if player == 1:
                        best_value, best_action = self.plugged_in_minimax.Max(history_copy[-1], self.minimax_max_depth, float('-inf'), float('inf'), player)
                    else:
                        best_value, best_action = self.plugged_in_minimax.Min(history_copy[-1], self.minimax_max_depth, float('-inf'), float('inf'), player)
                break

        # Back-propagation
        #
        end_values = {1: best_value, 2: -best_value}
        for player, state in visited_states:
            if (player, state) not in stats:
                continue
            S = stats[(player, state)]
            S.visits += 1
            S.value += end_values[player]

class UCTWins(UCT):
    action_template = "{action}: {percent:.2f}% ({wins} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTWins, self).__init__(board, **kwargs)
        self.end_values = board.win_values

    def calculate_action_values(self, state, player, legal):
        actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        return sorted(
            ({'action': p,
              'percent': 100 * self.stats[(player, S)].value / self.stats[(player, S)].visits,
              'wins': self.stats[(player, S)].value,
              'plays': self.stats[(player, S)].visits}
             for p, S in actions_states),
            key=lambda x: (x['percent'], x['plays']),
            reverse=True
        )


class UCTValues(UCT):
    action_template = "{action}: {average:.1f} ({sum} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTValues, self).__init__(board, **kwargs)
        self.end_values = board.points_values

    def calculate_action_values(self, state, player, legal):
        actions_states = ((p, self.board.next_state(state, p)) for p in legal)
        return sorted(
            ({'action': p,
              'average': self.stats[(player, S)].value / self.stats[(player, S)].visits,
              'sum': self.stats[(player, S)].value,
              'plays': self.stats[(player, S)].visits}
             for p, S in actions_states),
            key=lambda x: (x['average'], x['plays']),
            reverse=True
        )
