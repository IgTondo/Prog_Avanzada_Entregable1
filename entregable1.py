import numpy as np
import os

PLAYERS = 4
PRIZES = 3
PUNISHMENTS = 2

BOARD_LEN = 30
WIDTH = 9
HEIGHT = (BOARD_LEN - 2 * WIDTH + 4) // 2
CELL_WIDTH = 9
PLAYER_COLORS = ("\033[31m", "\033[34m", "\033[32m", "\033[33m")  # red, blue, green, yellow
RESET_COLOR = "\033[0m"

def throw_dice():
    return np.random.randint(1, 7)

def create_board():
    board = [0 for i in range(BOARD_LEN)]
    for i in range(PRIZES):
        prize_index = np.random.randint(1, BOARD_LEN )
        while board[prize_index] != 0:
            prize_index = np.random.randint(0, BOARD_LEN)
        board[prize_index] = 1
    for i in range(PUNISHMENTS):
        punishment_index = np.random.randint(0, BOARD_LEN)
        while board[punishment_index] != 0:
            punishment_index = np.random.randint(0, BOARD_LEN)
        board[punishment_index] = -1
    return board

def print_board(board, players_positions):
    assert len(board) == 2 * WIDTH + 2 * (HEIGHT - 2)
    assert len(players_positions) == PLAYERS
    assert all(0 <= position < len(board) for position in players_positions)

    symbols = {0: ".", 1: "P", -1: "C"}
    
    # Define a lambda function to format each cell with its index and symbol, centered within the cell width.
    def cell(index):
        players = [f"{PLAYER_COLORS[player]}J{RESET_COLOR}"
                   for player, position in enumerate(players_positions) if position == index]
        label = f"{symbols[board[index]]}"
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
        left = len(board) - row
        right = WIDTH + row - 1
        print(f"|{cell(left)}|{' ' * middle_width}|{cell(right)}|")
        if row < HEIGHT - 2:
            print(side_border)
    print(full_border)
    bottom_start = WIDTH + HEIGHT - 2
    print("|" + "|".join(cell(bottom_start + WIDTH - 1 - column)
                           for column in range(WIDTH)) + "|")
    print(full_border)
    
def game_loop():
    for player in range(PLAYERS):
        os.system('cls' if os.name == 'nt' else 'clear')
        print_board(board, players_positions)
        input(f"Player {player + 1}, press Enter to throw the dice...")
        dice_value = throw_dice()
        print(f"Player {player + 1} rolled a {dice_value}.")
            
        players_positions[player] += dice_value
        if players_positions[player] >= BOARD_LEN:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Player {player + 1} has reached the end of the board and wins!")
            exit()
    
if __name__ == "__main__":
    board = create_board()
    players_positions = [0 for _ in range(PLAYERS)]
    while True:
        game_loop()
                
