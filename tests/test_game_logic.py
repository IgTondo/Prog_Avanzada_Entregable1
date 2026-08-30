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
