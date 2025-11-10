# Crypto Quantitative Trading System

**Professional-Grade Algorithmic Trading Strategies for Cryptocurrency Markets**

Built with the mindset of a senior quantitative trader at Jump Trading, this system implements four distinct, battle-tested strategies designed for statistical arbitrage and market microstructure exploitation in crypto perpetual futures markets.

---

## 🎯 Performance Targets

All strategies are designed to meet or exceed:

- **Annual Return:** >40%
- **Sharpe Ratio:** >1.5
- **Max Drawdown:** <15%
- **Win Rate:** >58%

---

## 📊 Strategy Suite

### Strategy 1: Liquidity Imbalance Mean Reversion

**Core Premise:** Large aggressive market orders create temporary price dislocations. Capture the snap-back as liquidity replenishes.

**Mechanics:**
- Detect abnormally large orders (volume >4σ above mean)
- Enter counter-trend on RSI confirmation
- Tight stops (0.15%), quick targets (0.25%)
- Hold time: 5-60 minutes

**Target Performance:**
- Annual Return: >40%
- Sharpe Ratio: >1.5
- Win Rate: ~62%
- Profit Factor: ~1.8

**Key Features:**
- Volume z-score analysis
- Spread consumption measurement
- RSI reversal confirmation
- Dynamic position sizing

### Strategy 2: Volatility Normalization Breakout

**Core Premise:** Volatility is cyclical. Breakouts from compressed Bollinger Bands with volume confirmation have momentum follow-through.

**Mechanics:**
- Detect compression (bandwidth in lowest 20th percentile)
- Enter on breakout with volume >1.2x average
- Stop at BB middle, trailing stop (Chandelier 3x ATR)
- Hold time: Hours to days

**Target Performance:**
- Annual Return: >40%
- Sharpe Ratio: >1.5
- Win Rate: ~58%
- Profit Factor: ~2.1

**Key Features:**
- Bollinger Bandwidth percentile analysis
- Volume breakout confirmation
- Chandelier Exit trailing stops
- ATR-scaled position sizing

### Strategy 3: Spot-Perpetual Basis Funding Arbitrage

**Core Premise:** Market-neutral arbitrage capturing funding rate inefficiencies between spot and perpetual futures.

**Mechanics:**
- Long spot / Short perp when funding >0.05% (8h)
- Maintain delta-neutral hedge (1:1 ratio)
- Monitor funding rate and basis convergence
- Hold until funding deteriorates

**Target Performance:**
- Annual Return: >40%
- Sharpe Ratio: >2.0
- Win Rate: ~75%
- Profit Factor: ~2.5

**Key Features:**
- Funding rate analysis and persistence checks
- Basis spread monitoring
- Delta-neutral hedging
- Low volatility (market-neutral)

### Strategy 4: Dynamic Funding Rate Cycle Arbitrage

**Core Premise:** Enhanced funding arbitrage with cycle detection, dynamic hedging, and optimal timing for superior yield capture.

**Mechanics:**
- FFT-based funding cycle detection
- Dynamic hedge ratios (0.8-1.2) based on momentum
- Enter during optimal windows (hours before funding)
- Position sizing scaled to funding percentile

**Target Performance:**
- Annual Return: >45%
- Sharpe Ratio: >2.2
- Win Rate: ~80%
- Profit Factor: ~2.8

**Key Features:**
- Fourier Transform cycle detection
- Dynamic hedge ratio adjustment
- Timing optimization
- Compound funding yields

---

## 🏗️ System Architecture

```
bybit/
├── strategies/              # Trading strategies
│   ├── base_strategy.py
│   ├── liquidity_imbalance_mean_reversion.py
│   ├── volatility_normalization_breakout.py
│   ├── spot_perp_basis_arbitrage.py
│   └── dynamic_funding_rate_arbitrage.py
│
├── backtest/               # Backtesting framework
│   ├── backtester.py       # High-performance backtest engine
│   ├── metrics.py          # Performance analytics
│   └── data_loader.py      # Market data management
│
├── risk/                   # Risk management
│   ├── risk_manager.py     # Portfolio risk controls
│   └── position_sizer.py   # Position sizing algorithms
│
├── utils/                  # Utilities
│   ├── indicators.py       # Technical indicators
│   ├── signal_generator.py # Trade signal formatting
│   └── helpers.py          # Helper functions
│
├── config/                 # Configuration
│   └── config.py           # Strategy and system config
│
├── execution/              # Live trading (framework)
│   └── __init__.py
│
└── main.py                 # Entry point

```

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd bybit

# Install dependencies
pip install -r requirements.txt
```

### Run Examples

```bash
# Run all strategies
python main.py

# Run specific strategy
python main.py --strategy 1  # Liquidity Imbalance
python main.py --strategy 2  # Volatility Breakout
python main.py --strategy 3  # Spot-Perp Arbitrage
python main.py --strategy 4  # Dynamic Funding
```

### Basic Usage

```python
from config.config import LiquidityImbalanceConfig
from strategies import LiquidityImbalanceMeanReversion
from backtest import Backtester, DataLoader
from risk import RiskManager, PositionSizer

# Configure strategy
config = LiquidityImbalanceConfig(
    assets=["BTC/USDT:USDT"],
    timeframe="5m"
)

# Load market data
loader = DataLoader()
data = loader.generate_synthetic_data(
    symbol="BTC/USDT",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Initialize components
risk_manager = RiskManager(config.risk)
position_sizer = PositionSizer(portfolio_value=100_000)

# Create strategy
strategy = LiquidityImbalanceMeanReversion(
    config=config,
    risk_manager=risk_manager,
    position_sizer=position_sizer
)

# Run backtest
backtester = Backtester(config)
metrics = backtester.run(strategy, {"BTC/USDT:USDT": data})

# View results
print(metrics)
```

---

## 📈 Signal Output Format

Each strategy generates detailed trade signals:

```
================================================================================
TRADE SIGNAL GENERATED
================================================================================
Timestamp:     2024-01-15 14:32:00 UTC
STRATEGY:      LiquidityImbalanceMeanReversion
ASSET:         BTC/USDT:USDT
TIMEFRAME:     5m
DIRECTION:     LONG
CONFIDENCE:    75.0%

ENTRY PRICE ZONE: $50,150.00 - $50,200.00

JUSTIFICATION & MARKET CONTEXT:
────────────────────────────────────────────────────────────────────────────
1. Trigger Condition:
   Large market SELL order detected: Volume 4.2σ above mean (850,000 USDT).
   Price moved through 80% of the spread, dropping 0.85%. RSI(6) at 28.4
   (oversold), now showing bullish reversal with price recovering.

2. Market State:
   Recent volatility: 0.42% (ATR: $245.50). Price had been consolidating
   in a 1.2% range for 12 periods. Liquidity shock created temporary
   dislocation.

3. Edge Rationale:
   Backtests show 62.0% win rate for this setup, with profit factor of 1.8.
   Edge from market maker liquidity replenishment and mean reversion
   within 60 minutes.

4. Risk Assessment:
   Primary risk: Start of larger downtrend. Mitigated by tight 0.15% stop,
   0.25% profit target, max 60-minute hold, and 0.5% portfolio risk sizing.

EXECUTION PARAMETERS:
────────────────────────────────────────────────────────────────────────────
• Entry:           $50,175 (Limit Order)
• Stop-Loss:       $50,025 (0.30%)
• Take-Profit:     $50,300 (0.25%)
• Risk/Reward:     1.67

• Position Size:   2.5% of portfolio ($2,500)
• Risk Amount:     0.5% of portfolio
• Leverage:        3.0x

================================================================================
```

---

## 🔧 Configuration

### Risk Parameters

```python
from config.config import RiskConfig

risk_config = RiskConfig(
    max_portfolio_risk=0.02,        # Max 2% risk per trade
    max_position_size=0.25,         # Max 25% per position
    max_leverage=5.0,               # Max 5x leverage
    max_daily_drawdown=0.05,        # 5% daily DD limit
    max_weekly_drawdown=0.10,       # 10% weekly DD limit
    max_monthly_drawdown=0.15,      # 15% monthly DD limit
    use_kelly_sizing=True,          # Use Kelly Criterion
    kelly_fraction=0.25,            # 1/4 Kelly for safety
)
```

### Strategy Parameters

Each strategy has customizable parameters. Example:

```python
from config.config import LiquidityImbalanceConfig

config = LiquidityImbalanceConfig(
    assets=["BTC/USDT:USDT", "ETH/USDT:USDT"],
    timeframe="5m",
)

# Customize parameters
config.params.volume_sigma_threshold = 4.2
config.params.rsi_oversold = 30
config.params.profit_target_pct = 0.0025
config.params.stop_loss_pct = 0.0015
```

---

## 📊 Performance Metrics

The system tracks comprehensive metrics:

- **Returns:** Total, Annual, Monthly
- **Risk-Adjusted:** Sharpe, Sortino, Calmar Ratios
- **Risk:** Max Drawdown, Volatility, VaR, CVaR
- **Trade Stats:** Win Rate, Profit Factor, Avg Win/Loss
- **Higher Moments:** Skewness, Kurtosis

---

## 🔬 Backtesting Features

- **Realistic Slippage:** 2 bps default
- **Fees:** Maker 0.02%, Taker 0.06%
- **Latency Simulation:** 50ms execution delay
- **Position Management:** Automatic stop-loss and take-profit
- **Risk Controls:** Real-time drawdown monitoring
- **Performance Analytics:** 20+ metrics

---

## 🎓 Strategy Improvement Areas

As specified in the requirements, three areas for iterative improvement:

### 1. Signal Refinement
- **On-chain data integration:** Large entity flow tracking
- **Time-of-day filters:** Higher mean-reversion during specific hours
- **Cross-asset confirmation:** Multi-market signal validation
- **Machine learning enhancement:** Predict liquidity event persistence

### 2. Dynamic Risk Sizing
- **Kelly Criterion optimization:** Real-time win rate and Sharpe tracking
- **Volatility regime adjustment:** Increase size in low-vol, decrease in high-vol
- **Correlation-based scaling:** Reduce exposure during high cross-asset correlation
- **Drawdown-adjusted sizing:** Scale down after losses, scale up after wins

### 3. Portfolio-Level Overlay
- **Correlation monitoring:** Reduce exposure when strategies are correlated
- **Risk aggregation:** Total portfolio VaR and stress testing
- **Capital allocation:** Dynamic capital distribution across strategies
- **Regime detection:** Shift strategy weights based on market regime

---

## ⚠️ Risk Disclosure

**THIS IS A RESEARCH AND EDUCATIONAL PROJECT**

- Crypto trading carries significant risk of capital loss
- Past performance does not guarantee future results
- Use appropriate position sizing and risk management
- Test thoroughly in paper trading before live deployment
- Never risk more than you can afford to lose

---

## 🛠️ Production Deployment

### Requirements for Live Trading

1. **Exchange API Setup:**
   - Configure API keys in `.env` file
   - Enable futures trading permissions
   - Set up IP whitelist

2. **Data Feeds:**
   - WebSocket connections for real-time data
   - Historical data for indicator calculation
   - Funding rate feeds (for arbitrage strategies)

3. **Infrastructure:**
   - Low-latency server (co-located preferred)
   - Redundant internet connections
   - Monitoring and alerting (Telegram, email)

4. **Risk Controls:**
   - Hard position limits
   - Circuit breakers on drawdown
   - Daily loss limits
   - Emergency shutdown procedures

### Forward Testing Protocol

Before live deployment:

1. **Paper Trading:** 30 days minimum
2. **Micro-capital Test:** 1-2% of target capital for 30 days
3. **Stress Testing:** Performance during high volatility
4. **Walk-Forward Optimization:** Rolling window validation

---

## 📚 References

### Quantitative Trading
- *Algorithmic Trading* by Ernest Chan
- *Quantitative Trading Strategies* by Lars Kestner
- *Inside the Black Box* by Rishi Narang

### Market Microstructure
- *Trading and Exchanges* by Larry Harris
- *Market Microstructure Theory* by Maureen O'Hara

### Risk Management
- *The Kelly Capital Growth Investment Criterion* by Leonard MacLean

---

## 📝 License

This project is for educational and research purposes. Use at your own risk.

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- Additional strategies (stat arb, pairs trading, etc.)
- Machine learning signal enhancement
- Multi-exchange arbitrage
- Options strategies
- Sentiment analysis integration

---

## 📧 Contact

For questions, collaborations, or institutional inquiries, please open an issue.

---

**Built for serious quantitative traders who think in Sharpe ratios, not hype.**

*"In God we trust. All others must bring data." - W. Edwards Deming*
