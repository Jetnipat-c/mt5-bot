from fastapi import APIRouter, HTTPException
from app.schemas import OpenOrderRequest, OrderResponse, PositionsResponse
from app import mt5_service

router = APIRouter(prefix="/trading", tags=["trading"])


@router.get("/positions", response_model=PositionsResponse)
def list_positions():
    positions = mt5_service.get_positions()
    return {"count": len(positions), "positions": positions}


@router.post("/orders", response_model=OrderResponse)
def open_order(req: OpenOrderRequest):
    try:
        ticket = mt5_service.open_order(
            symbol=req.symbol,
            action=req.action,
            lot=req.lot,
            price=req.price,
            sl=req.sl,
            tp=req.tp,
        )
        return {"success": True, "ticket": ticket, "message": f"{req.action} order opened"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/orders/{ticket}", response_model=OrderResponse)
def close_order(ticket: int, symbol: str = "EURUSD"):
    try:
        profit = mt5_service.close_order(ticket=ticket, symbol=symbol)
        return {"success": True, "ticket": ticket, "message": f"Closed with profit {profit}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
