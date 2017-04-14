import sys
import ai

class MiniMax(ai.AI):
    def __init__(self, board, **kwargs):
        super(MiniMax, self).__init__(board, **kwargs)

    def get_action(self):
        state = self.history[-1]
        player = self.board.current_player(state)
        # goal: player 1: max, player 2: min
        best_action = None
        if player == 1:
            value, best_action = self.Max(state, 10, float('-inf'), float('inf'), player)
        else:
            value, best_action = self.Min(state, 10, float('-inf'), float('inf'), player)
        #print "best_action: ", best_action
        return self.board.unpack_action(best_action)

    def Max(self, state, depth, alpha, beta, player):
        if depth == 0:
            return self.board.not_ended_points_values([state])[1], None  # return [point, action]

        legal = self.board.legal_actions([state])
        if not legal:
            if self.board.is_ended([state]):
                best = self.board.not_ended_points_values([state])[1]
                print 'max: time to return', 'best: ', best, 60 - depth, 'alpha: ', alpha, 'beta: ', beta# @DEBUG
                return best, None
            return Min(state, depth, alpha, beta, 2 - player)
        best = float('-inf')
        best_action = None

        for oneAction in legal:
            alpha = max(best, alpha)
            if alpha >= beta:
                break
            new_state = self.board.next_state(state, oneAction)
            value, min_action = self.Min(new_state, depth - 1, max(best, alpha), beta, 2 - player)
            if value > best:
                best = value
                best_action = oneAction
        return best, best_action

    def Min(self, state, depth, alpha, beta, player):
        if depth == 0:
            return self.board.not_ended_points_values([state])[1], None  # return [point, action]

        legal = self.board.legal_actions([state])
        if not legal:
            if self.board.is_ended([state]):
                best = self.board.not_ended_points_values([state])[1]
                print 'min: time to return', 'best: ', best, 60 - depth, 'alpha: ', alpha, 'beta: ', beta# @DEBUG
                return best, None
            return Max(state, depth, alpha, beta, 2 - player)

        best = float('inf')
        best_action = None

        for oneAction in legal:
            beta = min(best, beta)
            if alpha >= beta:
                break
            new_state = self.board.next_state(state, oneAction)
            value, max_action = self.Max(new_state, depth - 1, alpha, min(beta, best), 2 - player)
            if value < best:
                best = value
                best_action = oneAction
        return best, best_action
