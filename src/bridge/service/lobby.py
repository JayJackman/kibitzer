"""Lobby - manages tables."""

from __future__ import annotations

from .models import TableNotFoundError, TableSummary
from .table import Table


class Lobby:
    """Manages tables. In-memory, no persistence."""

    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def create_table(self) -> Table:
        """Create a new table with a unique ID."""
        table = Table()
        self._tables[table.id] = table
        return table

    def get_table(self, table_id: str) -> Table:
        """Get a table by ID. Raises TableNotFoundError if not found."""
        if table_id not in self._tables:
            raise TableNotFoundError(f"Table {table_id!r} not found")
        return self._tables[table_id]

    def list_tables(self) -> list[TableSummary]:
        """List all tables with summary info."""
        return [
            TableSummary(
                id=table.id,
                status=table.status,
                seats=dict(table.seats),
                num_players=sum(1 for p in table.seats.values() if p is not None),
            )
            for table in self._tables.values()
        ]

    def delete_table(self, table_id: str) -> None:
        """Remove a table. Raises TableNotFoundError if not found."""
        if table_id not in self._tables:
            raise TableNotFoundError(f"Table {table_id!r} not found")
        del self._tables[table_id]
