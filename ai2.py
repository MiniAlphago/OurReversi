# reference:
# https://github.com/jbradberry/mcts

from __future__ import division

import time
from math import log, sqrt
from random import choice


class Stat(object):
    __slots__ = ('value', 'visits')

    def __init__(self, value=0, visits=0):
        self.value = value
        self.visits = visits

class UCT(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.history = []
        self.stats = {}
	self.totalgametime = 0
        self.max_depth = 0
        self.data = {}
        time = 55    # should be 1 min but in case that time is over

	self.evalu={} #evaluation
	#modified by Joscar,totalgame to expand the depth
	self.totalgames = 0

        self.calculation_time = float(time)
        # self.calculation_time = float(kwargs.get('time', 3))  # @ST @NOTE Here calculation_time should be 1 min
        self.max_actions = int(kwargs.get('max_actions', 64))

        # Exploration constant, increase for more exploratory actions,
        # decrease to prefer actions with known higher win rates.
        self.C = float(kwargs.get('C', 1.96)) #Original1.4

    def update(self, state):
        self.history.append(self.board.pack_state(state))

    def display(self, state, action):
        state = self.board.pack_state(state)
        action = self.board.pack_action(action)
        return self.board.display(state, action)

    def winner_message(self, winners):
        return self.board.winner_message(winners)

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
        while (time.time() - begin < self.calculation_time) and self.max_depth<(6+int(self.totalgames/5000)): 
            self.run_simulation()
            games += 1
	self.totalgames +=games
	#self.totalgametime = self.totalgametime+games
        # Display the number of calls of `run_simulation` and the
        # time elapsed.
        self.data.update(games=games, max_depth=self.max_depth,
                         time=str(time.time() - begin))
        print self.data['games'], self.data['time']
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
	
	#self.max_actions = self.max_actions + int(self.totalgametime/10)
        stats = self.stats
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
	    #for test 
	    #print actions_states

            if all((player, S) in stats for p, S in actions_states):
                log_total = log(
                    sum(stats[(player, S)].visits for p, S in actions_states) or 1)
                value, action, state = max(
                    ((stats[(player, S)].value / (stats[(player, S)].visits or 1)) +
                     self.C * sqrt(log_total / (stats[(player, S)].visits or 1)), p, S)
                    for p, S in actions_states
                )
            else:
                # Otherwise, just make an arbitrary decision
		# evaluate and choose
		if(len(actions_states)==0 or len(actions_states)==1 or len(actions_states)==2):
	    	    action, state = choice(actions_states)
		else:
		    result=[]
		    result=self.evaluation(actions_states)
		# result = self.evaluation(actions_states)
                    action, state = choice(result)
		# for test
		# print action
		# print state

		

            history_copy.append(state)
	    
	    #for test
	    #print state

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
    
    def evaluation(self,actions_states):
	results=[]
	self.evalu={}
	for p,S in actions_states:
	    self.evalu[(p,S)]=0
	    if(p[0]==2 or p[0]==5):
		self.evalu[(p,S)]+=1
	    if(p[1]==2 or p[1]==5):
		self.evalu[(p,S)]+=1
	    if(p[0]==0 or p[0]==7):
		self.evalu[(p,S)]+=2
	    if(p[1]==0 or p[1]==7):
		self.evalu[(p,S)]+=2
	T = sorted(self.evalu.items(),key=lambda item:item[1],reverse=True)
	
	for t in range(len(T)):
	    results.append(T[t][0])  	
	#result = [(p,S) for i in T[i][0]]
	#print results
	return results[0:3]
	     

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
              'plays': self.stats[(player, S)].visits} for p, S in actions_states),
            key=lambda x: (x['percent'], x['plays']),
            reverse=True
        )


class UCTValues(UCT):
    action_template = "{action}: {average:.1f} ({sum} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTValues, self).__init__(board, **kwargs)
        self.end_values = board.points_values

    def calculate_action_values(self, state, player, legal):
        actions_states = [(p, self.board.next_state(state, p)) for p in legal]
        return sorted(
            ({'action': p,
              'average': self.stats[(player, S)].value / self.stats[(player, S)].visits,
              'sum': self.stats[(player, S)].value,
              'plays': self.stats[(player, S)].visits}
             for p, S in actions_states),
            key=lambda x: (x['average'], x['plays']),
            reverse=True
        )
