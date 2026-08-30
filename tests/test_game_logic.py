import pytest

import entregable1 as game


def state_at(position: int, *, current_player: int = 0) -> game.GameState:
    return game.GameState(
        board=[0] * 30,
        players=[
            game.Player(id=0, color=game.PLAYER_COLORS[0]),
            game.Player(id=1, color=game.PLAYER_COLORS[1]),
        ],
        players_positions=[position, 0],
        current_player=current_player,
        final_cell=29,
        skiped_players=[],
        mode="interactive",
    )


def test_reaching_final_cell_marks_winner_without_exiting():
    result = game.move_player(state_at(28), 1)

    assert result.players_positions == [29, 0]
    assert result.winner == 0


def test_competition_keeps_higher_roll_on_cell_and_moves_loser_back(monkeypatch):
    state = state_at(5)
    state = game.replace(state, players_positions=[5, 5])
    rolls = iter((6, 2))
    monkeypatch.setattr(game, "throw_dice", lambda: next(rolls))
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = game.competition(state, 0, 1)

    assert result.players_positions == [5, 3]
    assert result.current_player == 0


def test_competition_retries_after_tie_with_same_game_state(monkeypatch):
    state = game.replace(state_at(5), players_positions=[5, 5])
    rolls = iter((4, 4, 6, 1))
    monkeypatch.setattr(game, "throw_dice", lambda: next(rolls))
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = game.competition(state, 0, 1)

    assert result.players_positions == [5, 3]


def test_skipped_turn_returns_new_state_without_mutating_previous_state(monkeypatch):
    state = game.replace(state_at(0, current_player=1), skiped_players=[1])
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("No debería pedir una tirada"))

    result = game.game_loop(state, iter((1,)))

    assert state.skiped_players == [1]
    assert result.skiped_players == []
    assert result.current_player == 1


def test_skip_player_turn_announces_the_player_that_will_skip(capsys):
    result = game.skip_player_turn(state_at(0), 1)

    assert result.skiped_players == [1]
    assert "blue" in capsys.readouterr().out


def test_movement_prize_resolves_the_special_cell_it_reaches():
    board = [0] * 30
    board[5] = "p3"
    board[7] = "c1"
    state = game.replace(state_at(5), board=board)

    result = game.manage_colitions(state)

    assert result.players_positions == [7, 0]
    assert result.skiped_players == [0]


def test_game_loop_does_not_ask_for_input_after_a_winner_exists(monkeypatch):
    state = game.replace(state_at(29), winner=0)
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("No debería pedir input después de ganar"))

    result = game.game_loop(state, iter((0,)))

    assert result is state


def test_initialize_game_state_accepts_the_declared_prize_and_punishment_counts():
    state = game.initialize_game_state(
        2,
        "interactive",
        game.BOARD_LEN,
        game.PRIZES,
        game.PUNISHMENTS,
    )

    assert len(state.board) == game.BOARD_LEN
    assert state.board.count("p1") == 1
    assert state.board.count("c2") == 1


@pytest.mark.parametrize("player_count", (1, 5))
def test_initialize_game_state_rejects_unsupported_player_counts(player_count):
    with pytest.raises(ValueError, match="between 2 and 4"):
        game.initialize_game_state(
            player_count,
            "interactive",
            game.BOARD_LEN,
            game.PRIZES,
            game.PUNISHMENTS,
        )


def test_configure_game_collects_interactive_mode_and_player_names():
    answers = iter(("interactive", "2", "Ana", "Bruno"))

    state = game.configure_game(input_fn=lambda _: next(answers))

    assert state.mode == "interactive"
    assert [player.name for player in state.players] == ["Ana", "Bruno"]


def test_game_loop_accepts_an_input_function_for_non_console_adapters(monkeypatch):
    state = state_at(28)
    monkeypatch.setattr(game, "throw_dice", lambda: 1)

    result = game.game_loop(state, iter((0,)), input_fn=lambda _: "")

    assert result.winner == 0


def test_run_simulation_finishes_without_waiting_for_console_input(monkeypatch):
    state = game.replace(state_at(28), mode="simulation")
    monkeypatch.setattr(game, "throw_dice", lambda: 1)
    pauses = []

    result = game.run_simulation(state, pause_fn=lambda turn: pauses.append(turn), max_turns=3)

    assert result.winner == 0
    assert pauses == [1]


def test_game_loop_decorator_writes_a_log_entry(tmp_path, monkeypatch):
    log_file = tmp_path / "game.log"
    game.configure_logging(log_file)
    monkeypatch.setattr(game, "throw_dice", lambda: 1)

    game.game_loop(state_at(28), iter((0,)), input_fn=lambda _: "")

    assert "game_loop" in log_file.read_text(encoding="utf-8")


def test_compose_applies_game_state_transformations_in_order():
    advance_then_double = game.compose(lambda value: value * 2, lambda value: value + 1)

    assert advance_then_double(3) == 8


def test_resolve_turn_composes_movement_and_cell_effects():
    board = [0] * 30
    board[5] = "c1"
    state = game.replace(state_at(4), board=board)

    result = game.resolve_turn(state, 1, input_fn=lambda _: "")

    assert result.players_positions == [5, 0]
    assert result.skiped_players == [0]


def test_run_terminal_game_uses_simulation_mode(monkeypatch):
    state = game.replace(state_at(28), mode="simulation")
    monkeypatch.setattr(game, "configure_game", lambda input_fn: state)
    monkeypatch.setattr(game, "throw_dice", lambda: 1)

    result = game.run_terminal_game(input_fn=lambda _: "", pause_fn=lambda _: None)

    assert result.winner == 0
