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

        self.max_depth = 0
        self.data = {}
        self.totalgames=0
        self.calculation_time = float(kwargs.get('time', 56))  # @ST @NOTE Here calculation_time should be 1 min
        self.max_actions = int(kwargs.get('max_actions', 64))
        

        # Exploration constant, increase for more exploratory actions,
        # decrease to prefer actions with known higher win rates.
        self.C = float(kwargs.get('C', 1.96))

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
        while (time.time() - begin < self.calculation_time) and self.max_depth<(10+int(self.totalgames/5000)):
            self.run_simulation()
            games += 1
        self.totalgames +=games
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

    def run_simulation(self):
        # Plays out a "random" game from the current position,
        # then updates the statistics tables with the result.

        # A bit of an optimization here, so we have a local
        # variable lookup instead of an attribute access each loop.
        stats = self.stats

        visited_states = set()
        history_copy = self.history[:]
        state = history_copy[-1]
        player = self.board.current_player(state)

        expand = True
        for t in xrange(1, self.max_actions + 1):
            legal = self.board.legal_actions(history_copy)
            actions_states = [(p, self.board.next_state(state, p)) for p in legal]

            if all((player, S) in stats for p, S in actions_states):
                # If we have stats on all of the legal actions here, use UCB1.
                log_total = log(
                    sum(stats[(player, S)].visits for p, S in actions_states) or 1)
                value, action, state = max(
                    ((stats[(player, S)].value / (stats[(player, S)].visits or 1)) +
                     self.C * sqrt(log_total / (stats[(player, S)].visits or 1)), p, S)
                    for p, S in actions_states
                )
            else:
                # Otherwise, just make an arbitrary decision.
                #action, state = choice(actions_states)
                if(len(actions_states)<3):
                    action, state = choice(actions_states)
                else:
		    result=[]
		    result=evaluation(actions_states,state)
		# result = self.evaluation(actions_states)
                    action, state = choice(result)
		# for test
		# print action
		# print state

            history_copy.append(state)

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
        end_values = self.end_values(history_copy)
        for player, state in visited_states:
            if (player, state) not in stats:
                continue
            S = stats[(player, state)]
            S.visits += 1
            S.value += end_values[player]
     
def evaluation(actions_states,state):
    #evaluation contains 3 parts
    WEIGHTS = \
    [-5, -7, 8, -4, 4, 2, 4]
    P_RINGS = [0x4281001818008142,
               0x42000000004200,
               0x2400810000810024,
               0x24420000422400,
               0x1800008181000018,
               0x18004242001800,
               0x3C24243C0000]
    P_CORNER = 0x8100000000000081
    P_SUB_CORNER = 0x42C300000000C342
    FULL_MASK = 0xFFFFFFFFFFFFFFFF
    results=[]
    evalu={}
    BIT = [1 << n for n in range(64)]
    for p,S in actions_states:
        evalu[(p,S)]=0
        
        #stability
        mine_stab=0
        opp_stab=0
        p1_placed, p2_placed, previous, player = state
        mine = p1_placed if player == 1 else p2_placed
        opp = p2_placed if player == 1 else p1_placed

	m0 = mine & BIT[0] != 0
        m1 = mine & BIT[7] != 0
        m2 = mine & BIT[56] != 0
        m3 = mine & BIT[63] != 0
        o0 = opp & BIT[0] != 0
        o1 = opp & BIT[7] != 0
        o2 = opp & BIT[56] != 0
        o3 = opp & BIT[63] != 0

        if m0 != 1 and o0 != 1:
            mine_stab += (mine & BIT[1] != 0) + (mine & BIT[8] != 0) + (mine & BIT[9] != 0)
            opp_stab  += (opp  & BIT[1] != 0) + (opp  & BIT[8] != 0) + (opp  & BIT[9] != 0)
        if m1 != 1 and o1 != 1:
            mine_stab += (mine & BIT[6] != 0) + (mine & BIT[14] != 0) + (mine & BIT[15] != 0)
            opp_stab  += (opp  & BIT[6] != 0) + (opp  & BIT[14] != 0) + (opp  & BIT[15] != 0)
        if m2 != 1 and o2 != 1:
            mine_stab += (mine & BIT[48] != 0) + (mine & BIT[49] != 0) + (mine & BIT[57] != 0)
            opp_stab  += (opp  & BIT[48] != 0) + (opp  & BIT[49] != 0) + (opp  & BIT[57] != 0)
        if m3 != 1 and o3 != 1:
            mine_stab += (mine & BIT[62] != 0) + (mine & BIT[54] != 0) + (mine & BIT[55] != 0)
            opp_stab  += (opp  & BIT[62] != 0) + (opp  & BIT[54] != 0) + (opp  & BIT[55] != 0)

        scoreunstable = - 40.0 * (mine_stab - opp_stab)

        # piece difference
        mpiece = (m0 + m1 + m2 + m3) * 100.0
        for i in range(len(WEIGHTS)):
            mpiece += WEIGHTS[i] * count_bit(mine & P_RINGS[i])

        opiece = (o0 + o1 + o2 + o3) * 100.0
        for i in range(len(WEIGHTS)):
            opiece += WEIGHTS[i] * count_bit(opp  & P_RINGS[i])
        
        scorepiece = mpiece - opiece

        # mobility@Why only white conpute the mob value  
        mmob = count_bit(move_gen(mine, opp))
        scoremob = 20 * mmob

        evalu[(p,S)]=scorepiece + scoreunstable + scoremob

       #if(p[0]==2 or p[0]==5):
    #   evalu[(p,S)]+=1
       #if(p[1]==2 or p[1]==5):
	 #   evalu[(p,S)]+=1
	#if(p[0]==0 or p[0]==7):
        #   evalu[(p,S)]+=2
        #if(p[1]==0 or p[1]==7):
        #   evalu[(p,S)]+=2
    
    T = sorted(evalu.items(),key=lambda item:item[1],reverse=True)
	
    for t in range(len(T)):
        results.append(T[t][0])  	
	#result = [(p,S) for i in T[i][0]]
	#print results
    return results[0:3]
	
def count_bit(b):
    FULL_MASK = 0xFFFFFFFFFFFFFFFF
    b -=  (b >> 1) & 0x5555555555555555
    b  = (((b >> 2) & 0x3333333333333333) + (b & 0x3333333333333333))
    b  = ((b >> 4) + b)  & 0x0F0F0F0F0F0F0F0F
    return ((b * 0x0101010101010101) & FULL_MASK) >> 56     


def move_gen_sub(P, mask, dir):
    dir2 = long(dir * 2)
    flip1  = mask & (P << dir)
    flip2  = mask & (P >> dir)
    flip1 |= mask & (flip1 << dir)
    flip2 |= mask & (flip2 >> dir)
    mask1  = mask & (mask << dir)
    mask2  = mask & (mask >> dir)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    flip1 |= mask1 & (flip1 << dir2)
    flip2 |= mask2 & (flip2 >> dir2)
    return (flip1 << dir) | (flip2 >> dir)

def move_gen(P, O):
    FULL_MASK = 0xFFFFFFFFFFFFFFFF
    mask = O & 0x7E7E7E7E7E7E7E7E
    return ((move_gen_sub(P, mask, 1)
            | move_gen_sub(P, O, 8)
            | move_gen_sub(P, mask, 7)
            | move_gen_sub(P, mask, 9)) & ~(P|O)) & FULL_MASK


class UCTWins(UCT):
    action_template = "{action}: {percent:.2f}% ({wins} / {plays})"

    def __init__(self, board, **kwargs):
        super(UCTWins, self).__init__(board, **kwargs)
        self.end_values = board.win_values

    def calculate_action_values(self, state, player, legal):
        result=[]
	
        actions_states = [(p, self.board.next_state(state, p)) for p in legal]
        if len(actions_states)<3:
	    result = actions_states
        else:
	    result = evaluation(actions_states,self.history[-1])
        return sorted(
            ({'action': p,
              'percent': 100 * self.stats[(player, S)].value / self.stats[(player, S)].visits,
              'wins': self.stats[(player, S)].value,
              'plays': self.stats[(player, S)].visits}
             for p, S in result),
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
