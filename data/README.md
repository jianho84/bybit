# Data Directory

This directory stores market data for backtesting and analysis.

## Data Sources

### Recommended Exchanges
- **Bybit:** Primary, good API and data quality
- **Binance:** Large liquidity, comprehensive historical data
- **OKX:** Good for funding rate data

### Data Types Required

1. **OHLCV Data**
   - Timeframes: 1m, 5m, 15m, 1h, 4h
   - Format: timestamp, open, high, low, close, volume
   - Storage: Parquet or HDF5 for efficiency

2. **Funding Rate Data**
   - Required for Strategies 3 & 4
   - Format: timestamp, funding_rate
   - Frequency: Every 8 hours (or exchange-specific)

3. **Order Book Data (Optional)**
   - For advanced liquidity analysis
   - Format: timestamp, bids, asks (top N levels)

4. **Trade Data (Optional)**
   - For large order detection
   - Format: timestamp, price, volume, side

## Data Collection

### Using CCXT

```python
import ccxt
import pandas as pd

# Initialize exchange
exchange = ccxt.bybit({
    'enableRateLimit': True,
})

# Fetch OHLCV
ohlcv = exchange.fetch_ohlcv(
    'BTC/USDT',
    timeframe='5m',
    limit=1000
)

# Save to file
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df.to_parquet('data/btc_usdt_5m.parquet')
```

### Historical Data

For backtesting, download at least:
- **Directional strategies (1 & 2):** 6-12 months
- **Arbitrage strategies (3 & 4):** 3-6 months minimum

## Storage Structure

```
data/
├── ohlcv/
│   ├── btc_usdt_5m.parquet
│   ├── eth_usdt_5m.parquet
│   └── ...
├── funding/
│   ├── btc_usdt_funding.parquet
│   └── ...
├── orderbook/
│   └── ...
└── trades/
    └── ...
```

## Data Quality Checks

Before backtesting, verify:
- No missing timestamps
- No price anomalies (flash crashes, bad data)
- Volume is reasonable
- Funding rates are within expected range (-0.5% to +0.5%)
