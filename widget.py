import time, pygame

class Window(object):

    def __init__(self, width, height, title='', background_image_path=''):
        pygame.init()

        self.width, self.height, self.title = width, height, title
        if self.width and self.height:
            self.window = pygame.display.set_mode((self.width, self.height))
            if self.title: pygame.display.set_caption(self.title)

        if background_image_path:
            self.bgp = pygame.image.load(background_image_path)
            self.bgpw, self.bgph = self.bgp.get_width(), self.bgp.get_height()

        self.done_background = False

    def update(self):
        pygame.display.flip()

    def quit(self):
        pygame.quit()

    def reset_background(self):
        self.done_background = False

    def draw_background(self):
        if not self.bgp: return

        self.window.fill(0)
        for i in xrange((self.width+self.bgpw-1)/self.bgpw):  # @ST xrange() is similar to range(), @NOTE float type is valid here
            for j in xrange((self.height+self.bgph-1)/self.bgph):
                self.window.blit(self.bgp, (i * self.bgpw, j * self.bgph))  # @ST draw the background tile by tile

        self.update()
        self.done_background = True

    """ Should be included in a loop. """
    def draw_suface(self, anchor=(0,0), pos=(0,0), suface=None):
        loc = (anchor[0]+pos[0], anchor[1]+pos[1])[::-1]  # reverse  order
        if suface: self.window.blit(suface, loc)

    def draw_grid(self, anchor=(0,0), block=(0,0), grid=[[]], suface=()):
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                loc = (anchor[0]+i*block[0], anchor[1]+j*block[1])[::-1]
                self.window.blit(suface[-1], loc)
                if grid[i][j] != -1: self.window.blit(suface[grid[i][j]], loc)


class Keyboard(object):

    RANGE = 400

    def __init__(self):
        # ASCII VALUE RANGE
        self.keys = [False] * Keyboard.RANGE

    def monitor(self, onkeydown_callback=None):
        event = pygame.event.poll()
        if event.type == pygame.QUIT: return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                print('Closing window...')
                return False
            self.keys[event.key] = True
            if onkeydown_callback: onkeydown_callback(self.keys)
            self.keys[event.key] = False

        return True

class Board(object):

    MOVE = ((0,0),(-1,0),(0,1),(1,0),(0,-1))

    def __init__(self, window, player_number=2, entity_player_list=(0), player_title=(), height=0, width=0,  \
                 block_border=0, pieces_path=(), cursor_piece_path=''):
        self.window = window
        self.player_number = player_number
        self.entity_player_list = entity_player_list
        self.player_title = player_title
        self.height = height
        self.width = width
        self.pieces = ()

        self.locked  = False
        self.placed  = False
        self.pressed = False

        if pieces_path: self.pieces = tuple([pygame.image.load(pp) for pp in pieces_path if pp])
        if cursor_piece_path: self.cp = pygame.image.load(cursor_piece_path)

        # Boader overlapping.
        self.block_size = (self.pieces[0].get_height()-block_border, self.pieces[0].get_width()-block_border)
        self.anchor = (self.window.height/10, self.window.width/10)
        self.cursor = (3, 3)

    def is_locked(self):
        return self.locked

    def reset_lock(self):
        self.locked = False

    def get_player_status_text(self):
        formated_status_text = ['{who}\'s Turn', 'Flipping After {who}\'s Turn', '{who} Cannot Move',        \
                                '{who} Wins', 'Draw']
        who = self.player_title[self.rule.get_current_player()]

        which = 0
        if self.is_ending():
            winner = self.rule.get_winner()
            if len(winner) > 1: which = 4
            else: which, who = 3, self.player_title[winner[0]]
        elif not self.rule.has_feasible_location(): which = 2
        elif self.placed: which = 1

        return formated_status_text[which].format(who=who)

    def action(self, callbacks=()):
        # Cannot Move Case
        if not self.rule.has_feasible_location():
            self.rule.shift()
            self.locked = True
        # Flip itself Case
        elif self.placed:
            self.rule.shift(self.cursor)
            self.placed = False
            self.window.reset_background()
        # Need AI Case
        elif self.rule.get_current_player() not in self.entity_player_list:
            self.cursor = self.ai.get_play()
            self.rule.place(self.cursor)
            self.locked  = True
            self.placed  = True
            self.flutter_update()
        # Get Feasible Location Case
        elif self.pressed and self.rule.validate_loc(self.cursor):
            self.rule.place(self.cursor)
            self.locked  = True
            self.placed  = True
            self.pressed = False
            self.flutter_update()

        for cb in callbacks: cb()

    def update(self, keys):
        d = 0
        if keys[pygame.K_UP]: d = 1
        if keys[pygame.K_RIGHT]: d = 2
        if keys[pygame.K_DOWN]: d = 3
        if keys[pygame.K_LEFT]: d = 4
        self.pressed = False
        nxt_cursor = tuple([self.cursor[0]+Board.MOVE[d][0], self.cursor[1]+Board.MOVE[d][1]])
        if 0 <= nxt_cursor[0] < self.height and 0 <= nxt_cursor[1] < self.width:
            self.cursor = nxt_cursor
            self.flutter_update()
        if d != 0: return

        if keys[pygame.K_KP_ENTER] or keys[pygame.K_RETURN]:
            self.pressed = True

    def flutter_update(self):
        self.draw_self()

    def draw_self(self, state):
        self.window.draw_grid(self.anchor, self.block_size, state, self.pieces)
        self.window.draw_suface(self.anchor, (self.block_size[0]*self.cursor[0], self.block_size[1]*self.cursor[1]), self.cp)


class ScoreBoard(object):

    def __init__(self, window, player_number=2, board=None, pieces_path=()):
        self.window = window
        self.player_number = player_number
        self.board = board
        self.pieces = ()

        if pieces_path: self.pieces = tuple([pygame.image.load(pp) for pp in pieces_path if pp])

        self.anchor = (self.window.height/10, self.window.width/10*2+board.block_size[1]*board.width)
        self.score = [0] * self.player_number
        self.status_text = ''

    def update(self):
        self.score = map(str, self.board.rule.count())
        next_status_text = self.board.get_player_status_text()
        if self.status_text != next_status_text:
            self.status_text = next_status_text
            self.window.reset_background()

    def draw_self(self, score):
        # Drawing players' scores
        loc, padding_lr = [0, 0], self.window.width/100
        self.window.draw_suface(self.anchor, tuple(loc), self.pieces[0])

        loc[1] += self.board.block_size[1]+padding_lr
        font = pygame.font.Font(None, 80)
        text = ':'.join(score)
        size = font.size(text)
        padding_tb = (self.board.block_size[0]-size[1])/2
        loc[0] += padding_tb
        ren = font.render(text, True, (0,0,0))
        self.window.draw_suface(self.anchor, tuple(loc), ren)
        loc[0] -= padding_tb

        loc[1] += size[0]+padding_lr
        self.window.draw_suface(self.anchor, tuple(loc), self.pieces[1])

        # Drawing players' status
        loc = [self.board.block_size[0]+self.window.height/100, 0]
        font = pygame.font.Font(None, 30)
        ren = font.render(self.status_text, True, (0,0,0))
        self.window.draw_suface(self.anchor, tuple(loc), ren)
