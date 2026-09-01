import logging
import time
from dataclasses import dataclass, replace
from functools import reduce, wraps
from typing import Callable

import numpy as np

PRIZES = 3
PUNISHMENTS = 2

BOARD_LEN = 30
WIDTH = 9
HEIGHT = (BOARD_LEN - 2 * WIDTH + 4) // 2
CELL_WIDTH = 11
PLAYER_COLORS = ("\033[31m", "\033[34m", "\033[32m", "\033[33m")  # red, blue, green, yellow
RESET_COLOR = "\033[0m"
LOGGER = logging.getLogger("entregable1")

def configure_logging(log_file="game.log"):
    LOGGER.handlers.clear()
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    return log_file

def log_game_action(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        LOGGER.info("%s inició", function.__name__)
        result = function(*args, **kwargs)
        LOGGER.info("%s finalizó", function.__name__)
        return result
    return wrapped

def compose(*functions):
    def composed(value):
        return reduce(lambda current, function: function(current), reversed(functions), value)
    return composed

@dataclass(frozen=True)
class Player:
    id: int
    color: str
    name: str = ""

@dataclass(frozen=True)
class GameState:
    board: list
    players: list
    players_positions: list
    current_player: int
    final_cell: int
    skiped_players: list = None
    mode: str = "simulacion"
    winner: int | None = None
    simulation_delay: float = 0.0


@dataclass(frozen=True)
class GameIO:
    """Operaciones impuras que el motor del juego necesita delegar."""
    wait_for_roll: Callable[[str], None]
    wait_next_turn: Callable[[], None]
    choose_color: Callable[[tuple[str, ...]], str]
    roll_dice: Callable[[], int]
    show: Callable[[str], None]
    draw_board: Callable[[GameState], None]

def find_player_by_color(players, color):
    for player in players:
        if player.color == color:
            return player
    return None

def color_name_to_code(color: str) -> str:
    color_map = {
        "rojo": "\033[31m", "red": "\033[31m",
        "azul": "\033[34m", "blue": "\033[34m",
        "verde": "\033[32m", "green": "\033[32m",
        "amarillo": "\033[33m", "yellow": "\033[33m"
    }
    return color_map.get(color.lower(), "")

def get_player_color_name(player_id: int) -> str:
    color_map = {
        "\033[31m": "rojo",
        "\033[34m": "azul",
        "\033[32m": "verde",
        "\033[33m": "amarillo"
    }
    return color_map.get(PLAYER_COLORS[player_id], "desconocido")

def get_player_label(game_state: GameState, player_id: int) -> str:
    if game_state.players[player_id].name:
        return f"{game_state.players[player_id].name} ({get_player_color_name(player_id)})"
    return f"{game_state.players[player_id].color}"

def get_player_label_start(game_state: GameState, player_id: int) -> str:
    if game_state.players[player_id].name:
        return f"{game_state.players[player_id].name} ({get_player_color_name(player_id)})"
    return f"Jugador {game_state.players[player_id].color}"

def player_turns(player_count):
    current_player = 0
    while True:
        yield current_player
        current_player = (current_player + 1) % player_count

def throw_dice():
    return np.random.randint(1, 7)

def interactive_io() -> GameIO:
    def choose_color(colors: tuple[str, ...]) -> str:
        prompt = f"Ingrese el color del jugador que perderá el turno ({', '.join(colors)}): "
        color = input(prompt).strip().lower()
        while color not in colors:
            color = input(f"Color inválido. Ingrese uno de: {', '.join(colors)}: ").strip().lower()
        return color

    return GameIO(
        wait_for_roll=input,
        wait_next_turn=lambda: None,
        choose_color=choose_color,
        roll_dice=throw_dice,
        show=print,
        draw_board=print_board,
    )


def simulation_io(delay: float) -> GameIO:
    return GameIO(
        wait_for_roll=lambda _: None,
        wait_next_turn=lambda: time.sleep(delay),
        choose_color=lambda colors: colors[np.random.randint(0, len(colors))],
        roll_dice=throw_dice,
        show=print,
        draw_board=print_board,
    )


def move_player(game_state: GameState, player_id: int, steps: int) -> GameState:
    new_positions = game_state.players_positions.copy()
    new_positions[player_id] = max(new_positions[player_id] + steps, 0)

    if new_positions[player_id] >= game_state.final_cell:
        new_positions[player_id] = game_state.final_cell
        return replace(
            game_state,
            players_positions=new_positions,
            winner=player_id,
        )

    return replace(game_state, players_positions=new_positions)

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

    board[0] = "INICIO"
    board[-1] = "FIN"
    return board

def get_symbol(value):
    if value == 0:
        return "."
    elif value.startswith("p"):
        return "P"
    elif value.startswith("c"):
        return "C"
    return value

def initialize_game_state(player_count, mode, board_len, prize_count, punishment_count, names=None, simulation_delay=0.0) -> GameState:
    board = create_board(board_len, prize_count, punishment_count)
    names = names or [f"Jugador " for i in range(player_count)]
    players = [Player(id=i, color=PLAYER_COLORS[i], name=names[i]) for i in range(player_count)]
    players_positions = [0 for _ in range(player_count)]
    return GameState(
        board=board,
        players=players,
        players_positions=players_positions,
        current_player=0,
        skiped_players=[],
        final_cell=len(board) - 1,
        mode=mode,
        simulation_delay=simulation_delay,
    )

def get_player_names(player_count):
    names = []
    for index in range(player_count):
        name = input(f"Nombre del jugador {index + 1}: ").strip()
        while not name:
            name = input("Nombre inválido. Ingrese un nombre: ").strip()
        names.append(name)
    return names


def configure_game(min_player_count, max_player_count, modes, board_len, prize_count, punishment_count) -> GameState:
    mode = input(f"Modo de juego ({'/'.join(modes)}): ").strip().lower()
    while mode not in modes:
        mode = input(f"Modo inválido. Ingrese uno de los siguientes: {', '.join(modes)}: ").strip().lower()

    player_count = input("Cantidad de jugadores (2-4): ").strip()
    while not player_count.isdigit() or not min_player_count <= int(player_count) <= max_player_count:
        player_count = input(f"Cantidad inválida. Ingrese un valor entre {min_player_count} y {max_player_count}: ").strip()
    player_count = int(player_count)

    names = get_player_names(player_count) if mode == "interactivo" else None

    simulation_delay = 0.0
    if mode == "simulacion":
        delay = input("Segundos entre turnos: ").strip().replace(",", ".")
        while True:
            try:
                simulation_delay = float(delay)
                if simulation_delay >= 0:
                    break
            except ValueError:
                pass
            delay = input("Ingrese una cantidad de segundos válida (0 o mayor): ").strip().replace(",", ".")

    return initialize_game_state(player_count, mode, board_len, prize_count, punishment_count, names, simulation_delay)

def skip_player_turn(game_state: GameState, player_id: int) -> GameState:
    skipped_players = list(game_state.skiped_players or []) + [player_id]
    return replace(game_state, skiped_players=skipped_players)


def remove_skipped_player(game_state: GameState, player_id: int) -> GameState:
    skipped_players = [player for player in (game_state.skiped_players or []) if player != player_id]
    return replace(game_state, skiped_players=skipped_players)


def apply_prize1(game_state: GameState, player_id: int) -> GameState:
    return skip_player_turn(game_state, player_id)


def apply_prize2(game_state: GameState, dice_value: int) -> GameState:
    return move_player(game_state, game_state.current_player, dice_value)


def apply_prize3(game_state: GameState) -> GameState:
    return move_player(game_state, game_state.current_player, 2)


def apply_punishment_c2(game_state: GameState) -> GameState:
    return move_player(game_state, game_state.current_player, -3)


def prize1(game_state: GameState, io: GameIO) -> GameState:
    io.show("Premio 1: elija un color para que pierda su próximo turno.")
    colors = ("rojo", "azul", "verde", "amarillo")[:len(game_state.players)]
    color = io.choose_color(colors)
    player = find_player_by_color(game_state.players, color_name_to_code(color))

    if player is None:
        io.show(f"No hay ningún jugador con el color {color}.")
        return game_state

    io.show(f"{get_player_label_start(game_state, player.id)} perderá su próximo turno.")
    return apply_prize1(game_state, player.id)


def prize2(game_state: GameState, io: GameIO) -> GameState:
    io.show("Premio 2: tire el dado nuevamente y avance el valor obtenido.")
    player = get_player_label_start(game_state, game_state.current_player)
    io.wait_for_roll(f"{player}, presione Intro para tirar el dado...")
    dice_value = io.roll_dice()
    io.show(f"{player} tiró {dice_value}.")
    game_state = apply_prize2(game_state, dice_value)
    io.draw_board(game_state)
    return game_state


def prize3(game_state: GameState, io: GameIO) -> GameState:
    io.show("Premio 3: avance dos casillas.")
    game_state = apply_prize3(game_state)
    io.draw_board(game_state)
    return game_state


def punishment_c1(game_state: GameState, io: GameIO) -> GameState:
    io.show("Castigo 1: perderá su próximo turno.")
    return skip_player_turn(game_state, game_state.current_player)


def punishment_c2(game_state: GameState, io: GameIO) -> GameState:
    io.show("Castigo 2: retroceda tres casillas.")
    game_state = apply_punishment_c2(game_state)
    io.draw_board(game_state)
    return game_state


PRIZE_HANDLERS = {
    "p1": prize1,
    "p2": prize2,
    "p3": prize3,
}

PUNISHMENT_HANDLERS = {
    "c1": punishment_c1,
    "c2": punishment_c2,
}

def competition_loser(player1: int, player2: int, dice_value_p1: int, dice_value_p2: int) -> int | None:
    if dice_value_p1 == dice_value_p2:
        return None
    return player2 if dice_value_p1 > dice_value_p2 else player1


def competition(game_state: GameState, player1: int, player2: int, io: GameIO) -> GameState:
    while True:
        player1_label = get_player_label_start(game_state, player1)
        player2_label = get_player_label_start(game_state, player2)

        io.wait_for_roll(f"{player1_label}, presione Intro para tirar el dado...")
        dice_value_p1 = io.roll_dice()
        io.show(f"{player1_label} tiró {dice_value_p1}.")

        io.wait_for_roll(f"{player2_label}, presione Intro para tirar el dado...")
        dice_value_p2 = io.roll_dice()
        io.show(f"{player2_label} tiró {dice_value_p2}.")

        loser = competition_loser(player1, player2, dice_value_p1, dice_value_p2)
        if loser is None:
            io.show("Ambos jugadores sacaron el mismo valor. Vuelven a tirar.")
            continue
        break

    io.show(f"{get_player_label_start(game_state, loser)} perdió la competencia y retrocede dos casillas.")
    game_state = move_player(game_state, loser, -2)
    io.draw_board(game_state)

    while (
        len(list(filter(lambda position: position == game_state.players_positions[loser], game_state.players_positions))) > 1
        and game_state.players_positions[loser] > 0
    ):
        game_state = move_player(game_state, loser, -1)
        io.draw_board(game_state)
        io.show(
            f"{get_player_label_start(game_state, loser)} volvió a chocar y retrocede una casilla, "
            f"hasta la posición {game_state.players_positions[loser]}."
        )

    return game_state


def manage_collisions(game_state: GameState, io: GameIO) -> GameState:
    current_position = game_state.players_positions[game_state.current_player]
    cell_value = game_state.board[current_position]
    player_color = get_player_color_name(game_state.current_player)

    if len(list(filter(lambda x: x == current_position, game_state.players_positions))) > 1:
        colliding_players = [id for id, pos in enumerate(game_state.players_positions) if pos == current_position]
        io.show(f"Los jugadores {', '.join(get_player_label(game_state, id) for id in colliding_players)} chocaron en la casilla {current_position}.")
        game_state = competition(game_state, colliding_players[0], colliding_players[1], io)
    elif cell_value in PRIZE_HANDLERS:
        io.show(f"El jugador {player_color} cayó en el premio {cell_value}.")
        game_state = PRIZE_HANDLERS[cell_value](game_state, io)
    elif cell_value in PUNISHMENT_HANDLERS:
        io.show(f"El jugador {player_color} cayó en el castigo {cell_value}.")
        game_state = PUNISHMENT_HANDLERS[cell_value](game_state, io)

    moved_by_effect = game_state.players_positions[game_state.current_player] != current_position
    if game_state.winner is None and moved_by_effect:
        return manage_collisions(game_state, io)
    return game_state


def move_and_render(game_state: GameState, player_id: int, steps: int, io: GameIO) -> GameState:
    game_state = move_player(game_state, player_id, steps)
    io.draw_board(game_state)
    return game_state


def resolve_turn(game_state: GameState, dice_value: int, io: GameIO) -> GameState:
    return compose(
        lambda state: manage_collisions(state, io),
        lambda state: move_and_render(state, state.current_player, dice_value, io),
    )(game_state)

def run_simulation(game_state: GameState, io: GameIO, max_turns: int = 10000) -> GameState:
    turns = player_turns(len(game_state.players))
    turn_number = 0

    while game_state.winner is None:
        if turn_number >= max_turns:
            raise RuntimeError("La simulación superó el límite de turnos")
        game_state = game_loop(game_state, turns, io)
        turn_number += 1
    return game_state



def print_board(game_state: GameState):
    # assert len(game_state.board) == 2 * WIDTH + 2 * (HEIGHT - 2)
    # assert len(game_state.players_positions) == len(game_state.players)
    # assert all(0 <= position < len(game_state.board) for position in game_state.players_positions)
    
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

@log_game_action
def game_loop(game_state: GameState, turns, io: GameIO) -> GameState:
    if game_state.winner is not None:
        return game_state

    current_player = next(turns)

    game_state = replace(
        game_state,
        current_player=current_player
    )

    if game_state.skiped_players and current_player in game_state.skiped_players:
        io.show(f"{get_player_label_start(game_state, game_state.current_player)} pierde este turno.")
        io.wait_next_turn()
        return remove_skipped_player(game_state, current_player)
    
    player_color = get_player_label_start(game_state, game_state.current_player)

    io.wait_for_roll(f"Jugador {player_color}, presione Intro para tirar el dado...")
    dice_value = io.roll_dice()
    io.show(f"El jugador {player_color} sacó {dice_value}.")
    game_state = resolve_turn(game_state, dice_value, io)

    io.wait_next_turn()
    return game_state



def run_terminal_game(min_player_count, max_player_count, modes, board_len, prize_count, punishment_count) -> GameState:
    game_state = configure_game(min_player_count, max_player_count, modes, board_len, prize_count, punishment_count)
    io = interactive_io() if game_state.mode == "interactivo" else simulation_io(game_state.simulation_delay)
    configure_logging()
    io.show(
        f"Juego inicializado: {len(game_state.players)} jugadores, "
        f"{PRIZES} premios y {PUNISHMENTS} castigos."
    )
    io.draw_board(game_state)

    if game_state.mode == "simulacion":
        game_state = run_simulation(game_state, io)
    else:
        turns = player_turns(len(game_state.players))
        while game_state.winner is None:
            game_state = game_loop(game_state, turns, io)

    if game_state.winner is None:
        raise RuntimeError("El juego terminó sin ganador")
    winner = game_state.players[game_state.winner]
    io.show(f"{get_player_label_start(game_state, winner.id)} gana el juego.")
    return game_state


if __name__ == "__main__":
    min_player_count = 2
    max_player_count = 4
    modes = ("simulacion", "interactivo")
    board_len = BOARD_LEN
    prize_count = PRIZES
    punishment_count = PUNISHMENTS
    run_terminal_game(min_player_count, max_player_count, modes, board_len, prize_count, punishment_count)
