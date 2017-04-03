### Reversi Game

#### Dependencies
* pygame
* gevent

#### How to run

First, run the server
``` bash
python2 server.py
```

Then, run two clients to play against each other
``` bash
python2 player.py human  # for human player
python2 player.py mcts   # for AI
```
Or you can run two AIs and watch them to play.

#### Message Conventions

| Message Type | Format | Example |
| action | [a-h][1-8] | c3 |
| player | 1 or 2 | 1 |
