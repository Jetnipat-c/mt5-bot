import os
from mt5linux import MetaTrader5

_client: MetaTrader5 | None = None


def get_client() -> MetaTrader5:
    global _client
    if _client is None:
        host = os.getenv("MT5_HOST", "192.168.1.67")
        port = int(os.getenv("MT5_PORT", "18812"))
        _client = MetaTrader5(host=host, port=port)
        if not _client.initialize():
            raise RuntimeError(f"MT5 init failed: {_client.last_error()}")
    return _client


def open_order(symbol: str, action: str, lot: float, price: float, sl: float, tp: float) -> int | None:
    mt5 = get_client()

    sym_info = mt5.symbol_info(symbol)
    if sym_info is None:
        raise ValueError(f"Symbol {symbol} not found")
        
    digits = sym_info.digits
    price = round(price, digits)
    sl = round(sl, digits)
    tp = round(tp, digits)

    if action.upper() == "BUY":
        mt5_type = mt5.ORDER_TYPE_BUY
    elif action.upper() == "SELL":
        mt5_type = mt5.ORDER_TYPE_SELL
    else:
        raise ValueError("Invalid action")

    for filling in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": "python bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result.order
        elif result.retcode == 10030:
            continue
        else:
            raise RuntimeError(f"Order failed: {result.retcode} — {result.comment}")

    raise RuntimeError("No supported filling mode found")


def close_order(ticket: int, symbol: str) -> float:
    mt5 = get_client()
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        raise ValueError(f"Position {ticket} not found")

    pos = positions[0]
    tick = mt5.symbol_info_tick(symbol)
    price = tick.bid if pos.type == 0 else tick.ask
    close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY

    for filling in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "close by bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return pos.profit
        elif result.retcode == 10030:
            continue
        else:
            raise RuntimeError(f"Close failed: {result.retcode} — {result.comment}")

    raise RuntimeError("No supported filling mode found for closing")


def get_positions() -> list[dict]:
    mt5 = get_client()
    positions = mt5.positions_get() or []
    return [
        {
            "ticket": p.ticket,
            "symbol": p.symbol,
            "side": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "profit": p.profit,
        }
        for p in positions
    ]
