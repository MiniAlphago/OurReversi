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

#### Packets sniffed
```
{"message": 2, "type": "player"}
{"state": {"player": 1, "previous_player": 2, "pieces": [{"column": 3, "player": 2, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}]}, "type": "update", "board": null}
{"state": {"player": 2, "previous_player": 1, "pieces": [{"column": 2, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}]}, "type": "update", "board": null, "last_action": {"player": 1, "notation": "c4", "sequence": 2}}
```

```
{"message": 2, "type": "player"}
{"state": {"player": 1, "previous_player": 2, "pieces": [{"column": 3, "player": 2, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}]}, "type": "update", "board": null}
{"state": {"player": 2, "previous_player": 1, "pieces": [{"column": 2, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}]}, "type": "update", "board": null, "last_action": {"player": 1, "notation": "c4", "sequence": 2}}
{"message": "c5", "type": "action"}
{"state": {"player": 1, "previous_player": 2, "pieces": [{"column": 2, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 2, "player": 2, "type": "disc", "row": 4}, {"column": 3, "player": 2, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}]}, "type": "update", "board": null, "last_action": {"player": 2, "notation": "c5", "sequence": 3}}
{"state": {"player": 2, "previous_player": 1, "pieces": [{"column": 2, "player": 1, "type": "disc", "row": 3}, {"column": 3, "player": 1, "type": "disc", "row": 3}, {"column": 4, "player": 1, "type": "disc", "row": 3}, {"column": 2, "player": 1, "type": "disc", "row": 4}, {"column": 3, "player": 1, "type": "disc", "row": 4}, {"column": 4, "player": 2, "type": "disc", "row": 4}, {"column": 2, "player": 1, "type": "disc", "row": 5}]}, "type": "update", "board": null, "last_action": {"player": 1, "notation": "c6", "sequence": 4}}
```
