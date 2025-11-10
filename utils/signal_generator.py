"""
Signal Generator Module
======================
Generates formatted trade signals for strategies.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import pandas as pd


@dataclass
class TradeSignal:
    """Trade signal data structure."""

    strategy_name: str
    asset: str
    timeframe: str
    direction: str  # LONG or SHORT
    timestamp: datetime

    # Price levels
    entry_price: float
    entry_zone_min: float
    entry_zone_max: float
    stop_loss: float
    take_profit: Optional[float] = None
    trailing_stop_desc: Optional[str] = None

    # Position sizing
    position_size_pct: float = 0.0
    position_size_usd: float = 0.0
    position_size_units: float = 0.0
    risk_pct: float = 0.0
    leverage: float = 1.0

    # Signal justification
    trigger_condition: str = ""
    market_state: str = ""
    edge_rationale: str = ""
    risk_assessment: str = ""

    # Metadata
    confidence: float = 0.0  # 0-1
    expected_win_rate: float = 0.0
    expected_profit_factor: float = 0.0

    def to_dict(self) -> Dict:
        """Convert signal to dictionary."""
        return {
            'strategy': self.strategy_name,
            'asset': self.asset,
            'timeframe': self.timeframe,
            'direction': self.direction,
            'timestamp': self.timestamp,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size_pct': self.position_size_pct,
            'position_size_usd': self.position_size_usd,
            'risk_pct': self.risk_pct,
            'leverage': self.leverage,
            'confidence': self.confidence,
        }

    def format_output(self) -> str:
        """Format signal for console output."""
        risk_reward = (
            abs(self.take_profit - self.entry_price) /
            abs(self.entry_price - self.stop_loss)
            if self.take_profit and self.stop_loss != self.entry_price
            else 0
        )

        output = f"""
{'='*80}
TRADE SIGNAL GENERATED
{'='*80}
Timestamp:     {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
STRATEGY:      {self.strategy_name}
ASSET:         {self.asset}
TIMEFRAME:     {self.timeframe}
DIRECTION:     {self.direction}
CONFIDENCE:    {self.confidence:.1%}

ENTRY PRICE ZONE: ${self.entry_zone_min:,.2f} - ${self.entry_zone_max:,.2f}

JUSTIFICATION & MARKET CONTEXT:
{'─'*80}
1. Trigger Condition:
   {self.trigger_condition}

2. Market State:
   {self.market_state}

3. Edge Rationale:
   {self.edge_rationale}
   • Expected Win Rate: {self.expected_win_rate:.1%}
   • Expected Profit Factor: {self.expected_profit_factor:.2f}

4. Risk Assessment:
   {self.risk_assessment}

EXECUTION PARAMETERS:
{'─'*80}
• Entry Price:      ${self.entry_price:,.2f} (Limit Order)
• Stop-Loss:        ${self.stop_loss:,.2f} ({abs((self.entry_price - self.stop_loss) / self.entry_price * 100):.2f}%)
• Take-Profit:      {f'${self.take_profit:,.2f}' if self.take_profit else 'Dynamic'}
• Trailing Stop:    {self.trailing_stop_desc if self.trailing_stop_desc else 'None'}
• Risk/Reward:      {risk_reward:.2f}

• Position Size:    {self.position_size_pct:.2f}% of portfolio (${self.position_size_usd:,.2f})
• Position Units:   {self.position_size_units:.6f}
• Risk Amount:      {self.risk_pct:.2f}% of portfolio
• Leverage:         {self.leverage:.1f}x

{'='*80}
"""
        return output


class SignalGenerator:
    """Generates and manages trade signals."""

    def __init__(self):
        """Initialize signal generator."""
        self.signals_history = []

    def create_signal(
        self,
        strategy_name: str,
        asset: str,
        timeframe: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float] = None,
        trailing_stop_desc: Optional[str] = None,
        position_size_pct: float = 0.0,
        position_size_usd: float = 0.0,
        position_size_units: float = 0.0,
        risk_pct: float = 0.0,
        leverage: float = 1.0,
        trigger_condition: str = "",
        market_state: str = "",
        edge_rationale: str = "",
        risk_assessment: str = "",
        confidence: float = 0.0,
        expected_win_rate: float = 0.0,
        expected_profit_factor: float = 0.0,
    ) -> TradeSignal:
        """
        Create a new trade signal.

        Args:
            strategy_name: Name of the strategy
            asset: Trading pair
            timeframe: Chart timeframe
            direction: LONG or SHORT
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price (optional)
            trailing_stop_desc: Trailing stop description
            position_size_pct: Position size as % of portfolio
            position_size_usd: Position size in USD
            position_size_units: Position size in units
            risk_pct: Risk as % of portfolio
            leverage: Leverage multiplier
            trigger_condition: What triggered the signal
            market_state: Current market context
            edge_rationale: Why this trade has an edge
            risk_assessment: What could go wrong
            confidence: Confidence level (0-1)
            expected_win_rate: Historical win rate
            expected_profit_factor: Historical profit factor

        Returns:
            TradeSignal object
        """
        # Calculate entry zone (5% around entry)
        entry_zone_min = entry_price * 0.995
        entry_zone_max = entry_price * 1.005

        signal = TradeSignal(
            strategy_name=strategy_name,
            asset=asset,
            timeframe=timeframe,
            direction=direction,
            timestamp=datetime.utcnow(),
            entry_price=entry_price,
            entry_zone_min=entry_zone_min,
            entry_zone_max=entry_zone_max,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop_desc=trailing_stop_desc,
            position_size_pct=position_size_pct,
            position_size_usd=position_size_usd,
            position_size_units=position_size_units,
            risk_pct=risk_pct,
            leverage=leverage,
            trigger_condition=trigger_condition,
            market_state=market_state,
            edge_rationale=edge_rationale,
            risk_assessment=risk_assessment,
            confidence=confidence,
            expected_win_rate=expected_win_rate,
            expected_profit_factor=expected_profit_factor,
        )

        # Store in history
        self.signals_history.append(signal)

        return signal

    def get_recent_signals(self, n: int = 10) -> list:
        """Get N most recent signals."""
        return self.signals_history[-n:]

    def get_signals_by_strategy(self, strategy_name: str) -> list:
        """Get all signals for a specific strategy."""
        return [s for s in self.signals_history if s.strategy_name == strategy_name]

    def get_signals_by_asset(self, asset: str) -> list:
        """Get all signals for a specific asset."""
        return [s for s in self.signals_history if s.asset == asset]

    def export_signals_to_df(self) -> pd.DataFrame:
        """Export all signals to DataFrame."""
        if not self.signals_history:
            return pd.DataFrame()

        return pd.DataFrame([s.to_dict() for s in self.signals_history])

    def clear_history(self):
        """Clear signal history."""
        self.signals_history = []
