from pydantic import BaseModel
from typing import Optional


class OpenOrderRequest(BaseModel):
    action: str  # "BUY" or "SELL"
    symbol: str
    price: float
    sl: float
    tp: float
    lot: float = 0.01


class OrderResponse(BaseModel):
    success: bool
    ticket: Optional[int] = None
    message: str


class Position(BaseModel):
    ticket: int
    symbol: str
    side: str
    volume: float
    profit: float


class PositionsResponse(BaseModel):
    count: int
    positions: list[Position]
