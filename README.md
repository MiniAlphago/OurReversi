# Reversi Game

## Schedule

| Task | Due | Responsibility | Done |
| --- | --- | --- | :---: |
| Reconstruction | Apr 10, 24:00 UTC + 8 | [Stephen Tse](https://github.com/xjiajiahao) | ✓ |
| GUI | Apr 10, 24:00 UTC + 8  | [chchenhui](https://github.com/chchenhui) | `TODO` |
| MCTS | Apr 10, 24:00 UTC + 8  | [Joscar Jiang](https://github.com/JoscarJiang) | `TODO` |

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

### Or Run the Server Program on a Remote Server

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
A client send its move to the server and receives its opponent's move from the server in the `json` format `{"x": column, "y": row}`, where column and row are integers between 1 and 8, inclusively.

If one player cannot find a valid move, he/she **MUST** send a `{"x": -1, "y": -1}` message to server.

```
    1   2   3   4   5   6   7   8  
  |-------------------------------|  
1 |   |   |   |   |   |   |   |   |  
  |-------------------------------|  
2 |   |   |   |   |   |   |   |   |  
  |-------------------------------|  
3 |   |   |   |   |   |   |   |   |  
  |-------------------------------|  
4 |   |   |   | ● | ○ |   |   |   |  
  |-------------------------------|  
5 |   |   |   | ○ | ● |   |   |   |  
  |-------------------------------|  
6 |   |   |   |   |   |   |   |   |  
  |-------------------------------|  
7 |   |   |   |   |   |   |   |   |  
  |-------------------------------|    
8 |   |   |   |   |   |   |   |   |  
  |-------------------------------|  
```


### Examples
A player puts a piece at (3, 5).
``` json
{
    "x": 3,
    "y": 5
}
```

No valid move, abandon.
``` json
{
    "x": -1,
    "y": -1
}
```
