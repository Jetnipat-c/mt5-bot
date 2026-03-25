import pandas as pd
import pandas_ta as ta
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Using BackgroundScheduler or AsyncIOScheduler depending on FastAPI integration
from app.mt5_service import get_client, open_order, get_positions

logger = logging.getLogger(__name__)

# Global variables to manage bot state
bot_active = False
scheduler = AsyncIOScheduler()

# Strategy Configuration
SYMBOL = "EURUSD"
TIMEFRAME = 1  # 1-minute timeframe 
LOT = 0.01

def fetch_data(symbol: str, timeframe: int, count: int = 100) -> pd.DataFrame:
    """Fetch OHLCV data from MT5 and return as DataFrame."""
    mt5 = get_client()
    # mt5.TIMEFRAME_M1 is 1
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, count)
    if rates is None:
        logger.error(f"Failed to fetch data for {symbol}")
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def generate_signals(df: pd.DataFrame) -> str:
    """
    Basic EMA Crossover Strategy:
    BUY if EMA Fast (10) crosses above EMA Slow (20)
    SELL if EMA Fast (10) crosses below EMA Slow (20)
    Return "BUY", "SELL", or "HOLD"
    """
    if df.empty or len(df) < 20:
        return "HOLD"
        
    df.ta.ema(length=10, append=True)
    df.ta.ema(length=20, append=True)
    
    # Check the last two completed candles
    prev_fast = df['EMA_10'].iloc[-3]
    prev_slow = df['EMA_20'].iloc[-3]
    curr_fast = df['EMA_10'].iloc[-2]
    curr_slow = df['EMA_20'].iloc[-2]
    
    # Crossover condition
    if prev_fast <= prev_slow and curr_fast > curr_slow:
        return "BUY"
    elif prev_fast >= prev_slow and curr_fast < curr_slow:
        return "SELL"
    
    return "HOLD"

async def bot_tick():
    """Main loop logic executed every interval."""
    if not bot_active:
        return
        
    logger.info(f"Bot Tick run at {datetime.now()}")
    
    try:
        # 1. Fetch data
        df = fetch_data(SYMBOL, TIMEFRAME)
        
        # 2. Strategy evaluation
        signal = generate_signals(df)
        logger.info(f"Generated Signal: {signal} for {SYMBOL}")
        
        # 3. Execution limits
        # Prevent opening new orders if we already hold a position for this symbol
        positions = get_positions()
        has_open_position = any(p['symbol'] == SYMBOL for p in positions)
        
        if signal in ["BUY", "SELL"] and not has_open_position:
            logger.info(f"Executing {signal} for {SYMBOL}")
            # Arbitrary SL/TP for example purposes (20 pips)
            mt5 = get_client()
            tick = mt5.symbol_info_tick(SYMBOL)
            point = mt5.symbol_info(SYMBOL).point
            if signal == "BUY":
                price = tick.ask
                sl = price - 20 * 10 * point
                tp = price + 20 * 10 * point
            else:
                price = tick.bid
                sl = price + 20 * 10 * point
                tp = price - 20 * 10 * point
            order_id = open_order(SYMBOL, signal, LOT, price, sl, tp)
            logger.info(f"Order executed successfully with Ticket: {order_id}")
            
    except Exception as e:
        logger.error(f"Error during bot tick: {e}", exc_info=True)

def start_bot():
    global bot_active
    if not bot_active:
        bot_active = True
        logger.info("Bot started via command.")
        if not scheduler.get_jobs():
            # Run every minute on the 0th second
            scheduler.add_job(bot_tick, 'cron', second=0, id='bot_loop')
            scheduler.start()
            logger.info("Bot Scheduler started.")
    return {"status": "started", "active": bot_active}

def stop_bot():
    global bot_active
    bot_active = False
    logger.info("Bot stopped via command.")
    return {"status": "stopped", "active": bot_active}

def get_bot_status():
    return {"active": bot_active, "symbol": SYMBOL}
