# reference:
# https://github.com/jbradberry/mcts

from __future__ import division

import time
from math import log, sqrt
from random import choice
import ai
import minimax
import reversi
import eval

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
        self.interesting_legal_actions = []

    def get_action(self):

        # Causes the AI to calculate the best action from the
        # current game state and return it.

        self.max_depth = 0
        self.data = {}
        self.stats.clear()
        self.interesting_legal_actions[:] = []

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

        discs_num = self.board.count_discs(self.history[-1])
        max_searching_depth = self.max_actions - discs_num

        # @NOTE evaluate first so that we can prune
        actions_states = [(p, self.board.next_state(state, p)) for p in legal]
        legal_actions, scores = eval.evaluation(actions_states)
        avg_score = 0
        num_legal_actions = len(legal_actions)
        if player == 2:  # black, the actual score should be -score
            for i in range(num_legal_actions):
                scores[i] = - scores[i]
        # then we abandon actions with low scores
        for score in scores:
            avg_score += score
        avg_score = avg_score / num_legal_actions
        tmp_index = -1
        #print scores, avg_score
        for i in range(num_legal_actions):
            if scores[i] >= avg_score:
                self.interesting_legal_actions.append(legal_actions[i][0])
            #else:
            #    tmp_index = i
            #    break
        #if len(self.interesting_legal_actions) < 2 and tmp_index > 0:
        #    self.interesting_legal_actions.append(legal_actions[tmp_index][0])  # append one more action
        self.interesting_legal_actions = self.interesting_legal_actions[:4]  # we only consider the top 4 actions
        print "selected {0} / {1}".format(len(self.interesting_legal_actions), num_legal_actions)

        while time.time() - begin < self.calculation_time:
            self.run_simulation(max_searching_depth)
            games += 1

        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.data.update(games=games, max_depth=self.max_depth,
                         time=str(time.time() - begin))
        print 'games: {0}, time ellapsed: {1}'.format(self.data['games'], self.data['time'])
        print "Maximum depth searched:", self.max_depth

        # Store and display the stats for each possible action.
        self.data['actions'] = self.calculate_action_values(state, player, self.interesting_legal_actions)
        for m in self.data['actions']:
            print self.action_template.format(**m)

        # do minimax
        interesting_legal_action_values = []
        min_value = float('inf')
        max_value = float('-inf')
        for item in self.data['actions']:
            action = item['action']
            the_next_state = self.board.next_state(state, action)
            if the_next_state[3] == 1:
                value, best_action = self.plugged_in_minimax.Max(the_next_state, 5, float('-inf'), float('inf'), the_next_state[3])
            else:
                value, best_action = self.plugged_in_minimax.Min(the_next_state, 5, float('-inf'), float('inf'), the_next_state[3])
                value = -value
            interesting_legal_action_values.append(value)
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
        # regularize values
        if max_value == min_value:
            for i in range(len(interesting_legal_action_values)):
                interesting_legal_action_values[i] = 100.0
        else:
            for i in range(len(interesting_legal_action_values)):
                interesting_legal_action_values[i] = (interesting_legal_action_values[i] - min_value) / (max_value - min_value) * 100

        # weighted average
        w = 1
        if max_searching_depth > 0:
            w = min(self.max_depth / max_searching_depth, 1)
        for i in range(len(interesting_legal_action_values)):
            item = self.data['actions'][i]
            print item
            item['percent'] = w * item['percent'] + (1 - w) * interesting_legal_action_values[i]
        # sort again
        new_data = sorted(self.data['actions'],
            key=lambda x: (x['percent'], x['plays']),
            reverse=True)

        # # Pick the action with the highest average value.
        # best_action = None
        # if self.max_depth <= max_searching_depth - 2:  # if the algorithm does not converge
        #     if player == 1:
        #         value, best_action = self.plugged_in_minimax.Max(state, 6, float('-inf'), float('inf'), player)
        #     else:
        #         value, best_action = self.plugged_in_minimax.Min(state, 6, float('-inf'), float('inf'), player)
        # else:
        #     best_action = self.data['actions'][0]['action']
        print new_data
        best_action = new_data[0]['action']
        return self.board.unpack_action(best_action)

    # Here we run the simulation
    def run_simulation(self, max_searching_depth):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop. 6

        stats = self.stats
        visited_states = set()
        history_copy = self.history[:]
        state = history_copy[-1]
        player = self.board.current_player(state)

        expand = True

        # the most important part
        # Use UCB to evaluate the nodes and
        for t in xrange(1, self.max_actions + 1):
            if t == 1:
                legal = self.interesting_legal_actions
            else:
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
                if t > self.max_depth:
                    self.max_depth = t

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
