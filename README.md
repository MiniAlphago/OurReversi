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

Or you can run two AIs and watch them to play. If you want to run  an AI with GUI, use `-g` flag.
``` sh
python2 player.py mcts  # AI1
python2 player.py mcts2 -g #AI2
```

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

Once a client connects to a server successfully, you will be prompted:
```
Which player do you want to be, 1  ●  or 2  ○ ?
```
Then **only when there are two clients connected to the server can you input a number**. And if one client input a `1`, the other **MUST** input `2`, vice versa.

## Message Conventions

A client sends its action to the server and receives its opponent's action from the server in the `json` format `{"x": column, "y": row}`, where column and row are integers between 1 and 8, inclusively.

If one player cannot find a valid action, he/she **MUST** send a `{"x": -1, "y": -1}` message to the server.

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

No valid action, abandon.
``` json
{
    "x": -1,
    "y": -1
}
```
