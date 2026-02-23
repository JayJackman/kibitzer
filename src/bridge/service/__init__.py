"""Service layer — the stable API surface for all UIs."""

from .advisor import BiddingAdvisor
from .deal import deal
from .lobby import Lobby
from .models import (
    AuctionCompleteError,
    BiddingAdvice,
    DuplicateCardError,
    HandEvaluation,
    HandNotSetError,
    NotYourTurnError,
    Player,
    PlayerNotSeatedError,
    SeatEmptyError,
    SeatOccupiedError,
    TableNotFoundError,
    TableStatus,
    TableSummary,
    TableView,
    UnauthorizedBidError,
)
from .table import Table

__all__ = [
    "AuctionCompleteError",
    "BiddingAdvice",
    "BiddingAdvisor",
    "DuplicateCardError",
    "HandEvaluation",
    "HandNotSetError",
    "Lobby",
    "NotYourTurnError",
    "Player",
    "PlayerNotSeatedError",
    "SeatEmptyError",
    "SeatOccupiedError",
    "Table",
    "TableNotFoundError",
    "TableStatus",
    "TableSummary",
    "TableView",
    "UnauthorizedBidError",
    "deal",
]
