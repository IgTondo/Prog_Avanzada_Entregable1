import numpy as np
import os
from dataclasses import dataclass, replace

PRIZES = 3
PUNISHMENTS = 2

BOARD_LEN = 30
WIDTH = 9
HEIGHT = (BOARD_LEN - 2 * WIDTH + 4) // 2
CELL_WIDTH = 9
PLAYER_COLORS = ("\033[31m", "\033[34m", "\033[32m", "\033[33m")  # red, blue, green, yellow
RESET_COLOR = "\033[0m"

@dataclass(frozen=True)
class Player:
    id: int
    color: str

@dataclass(frozen=True)
class GameState:
    board: list
    players: list
    players_positions: list
    current_player: int
    final_cell: int
    skiped_players: list = None
    mode: str = "simulation"  

def find_player_by_color(players, color):
    for player in players:
        if player.color == color:
            return player
    return None

def transform_color(color: str) -> str:
    color_map = {
        "red": "\033[31m",
        "blue": "\033[34m",
        "green": "\033[32m",
        "yellow": "\033[33m"
    }
    return color_map.get(color.lower(), "")

def get_player_color(player_id: int) -> str:
    color_map = {
        "\033[31m": "red",
        "\033[34m": "blue",
        "\033[32m": "green",
        "\033[33m": "yellow"
    }
    return color_map.get(PLAYER_COLORS[player_id], "unknown")

def player_turns(player_count):
    current_player = 0
    while True:
        yield current_player
        current_player = (current_player + 1) % player_count

def throw_dice():
    return np.random.randint(1, 7)

def move_player(gameState: GameState, steps: int) -> GameState:
    current_player = gameState.current_player
    new_positions = gameState.players_positions.copy()
    new_positions[current_player] += steps

    if new_positions[current_player] < 0:
        new_positions[current_player] = 0

    if new_positions[current_player] >= BOARD_LEN:
        print(f"Player {current_player + 1} has reached the end of the board and wins!")
        exit()
        
    return GameState(
        board=gameState.board,
        players=gameState.players,
        players_positions=new_positions,
        current_player=gameState.current_player,
        final_cell=gameState.final_cell,
        skiped_players=gameState.skiped_players,
        mode=gameState.mode
    )

def create_board(board_cells, prizes, punishments):
    board = [0 for i in range(board_cells)]
    for i in range(prizes):
        prize_index = np.random.randint(1, board_cells - 2)
        while board[prize_index] != 0:
            prize_index = np.random.randint(1, board_cells - 2)
        board[prize_index] = f"p{i + 1}"
    for i in range(punishments):
        punishment_index = np.random.randint(1, board_cells - 2)
        while board[punishment_index] != 0:
            punishment_index = np.random.randint(1, board_cells - 2)
        board[punishment_index] = f"c{i + 1}"
    return board

def get_symbol(value):
    if value == 0:
        return "."
    elif value.startswith("p"):
        return "P"
    elif value.startswith("c"):
        return "C"

def initialize_game_state(player_count, mode, board_cells, prizes, punishments) -> GameState:
    board = create_board(board_cells, prizes, punishments)
    players = [Player(id=i, color=PLAYER_COLORS[i]) for i in range(player_count)]
    players_positions = [0 for _ in range(player_count)]
    return GameState(
        board=board,
        players=players,
        players_positions=players_positions,
        current_player=0,
        skiped_players=[],
        final_cell=len(board) - 1,
        mode=mode
    )

def skip_player_turn(game_state: GameState, player_id: int):
    skiped_players = (game_state.skiped_players.copy() if game_state.skiped_players else []) + [player_id]
    print(f"Player {get_player_color(game_state.current_player)} will skip their next turn.")
    return replace(game_state, skiped_players=skiped_players)

def prize1(gameState: GameState) -> bool:
    print("Prize 1: Skip the next turn of a player of your choice.")
    colors = ["red", "blue", "green", "yellow"][:len(gameState.players)]
    color = input(f"Enter the color of the player to skip ({', '.join(colors)}): ").strip().lower()
    player_color = transform_color(color)
    player = find_player_by_color(gameState.players, player_color)
    
    if player is None:
        print(f"No player found with color {color}.")
        return gameState
    
    return skip_player_turn(gameState, player.id)

def prize2(gameState: GameState) -> GameState:
    print("Prize 2: Throw the dice and move forward by the rolled value.")
    input(f"Player {get_player_color(gameState.current_player)}, press Enter to throw the dice...")
    dice_value = throw_dice()
    gameState = move_player(gameState, dice_value)
    return gameState

def prize3(gameState: GameState) -> GameState:
    print("Prize 3: Move forward by two positions.")
    gameState = move_player(gameState, 2)
    return gameState

def punishment_c2(gameState: GameState) -> GameState:
    print("Punishment 2: Move back by three positions.")
    gameState = move_player(gameState, -3)
    return gameState
PRIZES = {
    "p1": prize1,
    "p2": prize2,
    "p3": prize3
}

PUNISHMENTS = {
    "c1": lambda gameState: skip_player_turn(gameState, gameState.current_player),
    "c2": punishment_c2
}

def competition(game_state: GameState, player1, player2):
    players_positions = game_state.players_positions.copy()

    input(f"Player {get_player_color(player1)}, press Enter to throw the dice...")
    dice_value_p1 = throw_dice()
    print(f"Player {get_player_color(player1)} rolled a {dice_value_p1}.")

    input(f"{get_player_color(player2)}, press Enter to throw the dice...")
    dice_value_p2 = throw_dice()
    print(f"Player {get_player_color(player2)} rolled a {dice_value_p2}.")

    if dice_value_p1==dice_value_p2:
        print(f"Both players rolled the same value. They will roll again.")
        competition(player1, player2)
    
    loser = player1 if dice_value_p1>dice_value_p2 else player2
    print(f"Player {get_player_color(loser)} lost the competition and moves back two positions.")
    players_positions[loser] = players_positions[loser]-2

    while len(list(filter(lambda x: x == players_positions[loser], game_state.players_positions))) > 1 and players_positions[loser]>0:
        players_positions[loser]-=1
        print(f"Player {get_player_color(loser)} has collided with another player and moves back one position, to position {players_positions[loser]}.")
    
    return GameState(
        board=game_state.board,
        players=game_state.players,
        players_positions=players_positions,
        current_player=(game_state.current_player + 1) % len(game_state.players),
        skiped_players=game_state.skiped_players,
        mode=game_state.mode,
        final_cell=game_state.final_cell
    )

def manage_colitions(game_state: GameState) -> GameState:
    current_position = game_state.players_positions[game_state.current_player]
    cell_value = game_state.board[current_position]
    player_color = get_player_color(game_state.current_player)

    if len(list(filter(lambda x: x == current_position, game_state.players_positions))) > 1:
        colliding_players = [id for id, pos in enumerate(game_state.players_positions) if pos == current_position]
        print(f"Players {', '.join(get_player_color(id) for id in colliding_players)} have collided on cell {current_position}.")
        game_state = competition(game_state, colliding_players[0], colliding_players[1])
        print_board(game_state)
    elif cell_value in PRIZES:
        print(f"Player {player_color} landed on prize: {cell_value}.")
        game_state = PRIZES[cell_value](game_state)
        print_board(game_state)
    elif cell_value in PUNISHMENTS:
        print(f"Player {player_color} landed on punishment: {cell_value}.")
        game_state = PUNISHMENTS[cell_value](game_state)
        print_board(game_state)
    return game_state

def print_board(game_state: GameState):
    assert len(game_state.board) == 2 * WIDTH + 2 * (HEIGHT - 2)
    assert len(game_state.players_positions) == len(game_state.players)
    assert all(0 <= position < len(game_state.board) for position in game_state.players_positions)
    
    # Define a lambda function to format each cell with its index and symbol, centered within the cell width.
    def cell(index):
        players = [f"{PLAYER_COLORS[player]}J{RESET_COLOR}"
                   for player, position in enumerate(game_state.players_positions) if position == index]
        label = f"{get_symbol(game_state.board[index])}"
      
        visible_length = len(label) + len(players) + bool(players)
        return " " * ((CELL_WIDTH - visible_length) // 2) + label + (
            " " + "".join(players) if players else ""
        ) + " " * ((CELL_WIDTH - visible_length + 1) // 2)

    # Create the full border and side borders for the board display.
    full_border = "+" + "+".join("-" * CELL_WIDTH for _ in range(WIDTH)) + "+"
    
    # Calculate the width of the middle section of the board, which is the space between the left and right columns.
    middle_width = (WIDTH - 2) * (CELL_WIDTH + 1) - 1
    side_border = f"+{'-' * CELL_WIDTH}+{' ' * middle_width}+{'-' * CELL_WIDTH}+"

    print(full_border)
    print("|" + "|".join(cell(index) for index in range(WIDTH)) + "|")
    print(full_border)
    for row in range(1, HEIGHT - 1):
        left = len(game_state.board) - row
        right = WIDTH + row - 1
        print(f"|{cell(left)}|{' ' * middle_width}|{cell(right)}|")
        if row < HEIGHT - 2:
            print(side_border)
    print(full_border)
    bottom_start = WIDTH + HEIGHT - 2
    print("|" + "|".join(cell(bottom_start + WIDTH - 1 - column)
                           for column in range(WIDTH)) + "|")
    print(full_border)

def game_loop(game_state: GameState, turns):
    current_player = next(turns)

    game_state = replace(
        game_state,
        current_player=current_player
    )

    if game_state.skiped_players and current_player in game_state.skiped_players:
        print(f"Player {get_player_color(game_state.current_player)} is skipping their turn.")
        game_state.skiped_players.remove(current_player)
        return game_state
    
    player_color = get_player_color(game_state.current_player)

    input(f"Player {player_color}, press Enter to throw the dice...")
    dice_value = throw_dice()
    print(f"Player {player_color} rolled a {dice_value}.")
    game_state = move_player(game_state, dice_value)

    print_board(game_state)

    input("Press Enter to continue...")
    game_state = manage_colitions(game_state)
    return game_state


if __name__ == "__main__":
    player_count = 2
    mode = "interactive"
    prizes = 3
    punishments = 2
    game_state = initialize_game_state(player_count, mode, BOARD_LEN, prizes, punishments)
    turns = player_turns(len(game_state.players))
    print(f"Game initialized with {player_count} players, {prizes} prizes, and {punishments} punishments.")
    print("Let's start the game!")
    print_board(game_state)
    while True:
        game_state = game_loop(game_state, turns)
