# Reversi Game

## Schedule

| Task | Due Date | Responsibility | Done |
| --- | --- | --- | :---: |
| Reconstruction | Apr 10 | [Stephen Tse](https://github.com/xjiajiahao) | ✓ |
| GUI | Apr 10 | [chchenhui](https://github.com/chchenhui) | `TODO` |
| MCTS | Apr 10 | [Joscar Jiang](https://github.com/JoscarJiang) | `TODO` |

## Dependencies
* pygame
* gevent

## How to run

### Run the Server Program on Local Host
First, run the server
``` sh
python2 server.py
```

Then, run two clients to play against each other
``` sh
python2 player.py human -g  # for human player, add -g flag to enable gui
python2 player.py mcts   # for AI, @NOTE AI does not have gui by now
```
Or you can run two AIs and watch them to play.

### Run the Server Program on a Remote Server

First, run the server
``` sh
python2 server.py 0.0.0.0 4242  # you should specify address and port number
```

Then, run two clients to play against each other
``` sh
python2 player.py human -g http://qcloud.stse.me 4242 # for human player, add -g flag to enable gui, you should specify address and port number
python2 player.py mcts http://qcloud.stse.me 4242  # for AI, @NOTE AI does not have gui by now
```
### Note
If you shut down one client, to make things work again, you have to **shut down the server and the other client** and then restart them.

## Message Conventions

Message type:
* player
* update
* action
* decline
* error
* illegal

Note: update message has the following keys: state, type, board, last_action, winners, and points.
### Examples

When client connects to server, server sends the player number.
``` json
{
    "message": 2,
    "type": "player"
}
```

It's player 1's turn.
``` json
{
    "state": {
        "player": 1,
        "previous_player": 2,
        "pieces": [{
            "column": 3,
            "player": 2,
            "type": "disc",
            "row": 3
        }, {
            "column": 4,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 4
        }, {
            "column": 4,
            "player": 2,
            "type": "disc",
            "row": 4
        }]
    },
    "type": "update",
    "board": null
}
```

It's player 2's turn.
``` json
{
    "state": {
        "player": 2,
        "previous_player": 1,
        "pieces": [{
            "column": 2,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 4,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 4
        }, {
            "column": 4,
            "player": 2,
            "type": "disc",
            "row": 4
        }]
    },
    "type": "update",
    "board": null,
    "last_action": {
        "player": 1,
        "notation": "c4",
        "sequence": 2
    }
}

Player 2 sends its action to server.
``` json
{
    "message": "c5",
    "type": "action"
}
```

Player 1's turn again.
``` json
{
    "state": {
        "player": 1,
        "previous_player": 2,
        "pieces": [{
            "column": 2,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 4,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 2,
            "player": 2,
            "type": "disc",
            "row": 4
        }, {
            "column": 3,
            "player": 2,
            "type": "disc",
            "row": 4
        }, {
            "column": 4,
            "player": 2,
            "type": "disc",
            "row": 4
        }]
    },
    "type": "update",
    "board": null,
    "last_action": {
        "player": 2,
        "notation": "c5",
        "sequence": 3
    }
}
```

Player 2's turn again. Note that if someone wins, we will receive "winner" information
``` json
{
    "state": {
        "player": 2,
        "previous_player": 1,
        "pieces": [{
            "column": 2,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 4,
            "player": 1,
            "type": "disc",
            "row": 3
        }, {
            "column": 2,
            "player": 1,
            "type": "disc",
            "row": 4
        }, {
            "column": 3,
            "player": 1,
            "type": "disc",
            "row": 4
        }, {
            "column": 4,
            "player": 2,
            "type": "disc",
            "row": 4
        }, {
            "column": 2,
            "player": 1,
            "type": "disc",
            "row": 5
        }]
    },
    "winners": {"1": 1, "2": 0},
    "type": "update",
    "board": null,
    "last_action": {
        "player": 1,
        "notation": "c6",
        "sequence": 4
    }
}
```
