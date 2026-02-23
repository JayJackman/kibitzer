"""Tests for Lobby."""

import pytest

from bridge.model.auction import Seat
from bridge.service.lobby import Lobby
from bridge.service.models import Player, TableNotFoundError, TableStatus


class TestLobby:
    def test_create_table(self) -> None:
        lobby = Lobby()
        table = lobby.create_table()
        assert table.id
        assert table.status == TableStatus.WAITING

    def test_get_table(self) -> None:
        lobby = Lobby()
        table = lobby.create_table()
        retrieved = lobby.get_table(table.id)
        assert retrieved is table

    def test_get_nonexistent_raises(self) -> None:
        lobby = Lobby()
        with pytest.raises(TableNotFoundError, match="not found"):
            lobby.get_table("no-such-id")

    def test_list_tables(self) -> None:
        lobby = Lobby()
        t1 = lobby.create_table()
        t2 = lobby.create_table()
        summaries = lobby.list_tables()
        assert len(summaries) == 2
        ids = {s.id for s in summaries}
        assert t1.id in ids
        assert t2.id in ids

    def test_list_tables_shows_player_count(self) -> None:
        lobby = Lobby()
        table = lobby.create_table()
        table.join(Seat.NORTH, Player(name="Alice"))
        summaries = lobby.list_tables()
        assert summaries[0].num_players == 1

    def test_delete_table(self) -> None:
        lobby = Lobby()
        table = lobby.create_table()
        lobby.delete_table(table.id)
        with pytest.raises(TableNotFoundError):
            lobby.get_table(table.id)

    def test_delete_nonexistent_raises(self) -> None:
        lobby = Lobby()
        with pytest.raises(TableNotFoundError, match="not found"):
            lobby.delete_table("no-such-id")

    def test_list_empty(self) -> None:
        lobby = Lobby()
        assert lobby.list_tables() == []
