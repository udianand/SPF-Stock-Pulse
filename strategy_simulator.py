import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class InvestmentStrategy:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}
        self.trades_history: List[Dict] = []

    def simulate(self, hist_data: pd.DataFrame, strategy_type: str = 'ma_crossover', 
                risk_per_trade: float = 0.02) -> Dict:
        """
        Simulate investment strategy using historical price data

        Parameters:
        - hist_data: Historical price data
        - strategy_type: Type of trading strategy ('ma_crossover', 'rsi', 'macd')
        - risk_per_trade: Maximum risk per trade as percentage of portfolio
        """
        results = {
            'portfolio_value': [],
            'cash': [],
            'trades': [],
            'dates': []
        }

        # Prepare data with technical indicators
        data = self._prepare_data(hist_data)

        # Initialize simulation
        self.cash = self.initial_capital
        self.positions = {}
        self.trades_history = []

        for date, row in data.iterrows():
            # Generate trading signals based on selected strategy
            signal = self._generate_signal(row, strategy_type)

            # Calculate position size based on risk management
            risk_amount = self.cash * risk_per_trade
            atr = row.get('ATR', row['Close'] * 0.02)  # Default to 2% volatility if ATR not available
            position_size = risk_amount / atr

            # Execute trades based on signals
            if signal > 0 and self.cash > 0:  # Buy signal
                max_shares = min(position_size, (self.cash * 0.95) / row['Close'])  # Use max 95% of cash
                self._execute_trade(row['symbol'], max_shares, row['Close'], date, 'buy')
            elif signal < 0 and row['symbol'] in self.positions:  # Sell signal
                self._execute_trade(row['symbol'], self.positions[row['symbol']], 
                                row['Close'], date, 'sell')

            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(data.loc[date])

            # Store results
            results['portfolio_value'].append(portfolio_value)
            results['cash'].append(self.cash)
            results['dates'].append(date)

        return self._calculate_metrics(results)

    def _prepare_data(self, hist_data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to historical data"""
        data = hist_data.copy()

        # Moving averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_12'] = data['Close'].ewm(span=12).mean()
        data['EMA_26'] = data['Close'].ewm(span=26).mean()

        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['Signal_Line'] = data['MACD'].ewm(span=9).mean()

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Average True Range (ATR)
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        data['ATR'] = true_range.rolling(window=14).mean()

        return data

    def _generate_signal(self, data: pd.Series, strategy_type: str) -> float:
        """
        Generate trading signal based on selected strategy
        Returns: float between -1 (strong sell) and 1 (strong buy)
        """
        signal = 0.0

        if strategy_type == 'ma_crossover':
            # Moving average crossover strategy
            if data['SMA_20'] > data['SMA_50']:
                signal += 0.5
            else:
                signal -= 0.5

            # Add trend strength
            trend_strength = abs(data['SMA_20'] - data['SMA_50']) / data['SMA_50']
            signal *= (1 + trend_strength)

        elif strategy_type == 'rsi':
            # RSI strategy
            if data['RSI'] < 30:  # Oversold
                signal += 1
            elif data['RSI'] > 70:  # Overbought
                signal -= 1

        elif strategy_type == 'macd':
            # MACD strategy
            if data['MACD'] > data['Signal_Line']:
                signal += 0.5
            else:
                signal -= 0.5

            # Add momentum strength
            momentum = abs(data['MACD'] - data['Signal_Line'])
            signal *= (1 + momentum)

        return np.clip(signal, -1, 1)

    def _execute_trade(self, symbol: str, shares: float, price: float, 
                     date: datetime, trade_type: str):
        """Execute trade and record it"""
        if trade_type == 'buy':
            cost = shares * price
            if cost <= self.cash:
                self.cash -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + shares
        else:  # sell
            proceeds = shares * price
            self.cash += proceeds
            del self.positions[symbol]

        self.trades_history.append({
            'date': date,
            'symbol': symbol,
            'type': trade_type,
            'shares': shares,
            'price': price,
            'value': shares * price
        })

    def _calculate_portfolio_value(self, current_prices) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(shares * current_prices['Close']
                           for symbol, shares in self.positions.items())
        return self.cash + positions_value

    def _calculate_metrics(self, results: Dict) -> Dict:
        """Calculate comprehensive performance metrics"""
        portfolio_values = np.array(results['portfolio_value'])
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

        # Calculate metrics
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital
        sharpe_ratio = np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns) if len(daily_returns) > 0 else 0
        max_drawdown = np.min(portfolio_values / np.maximum.accumulate(portfolio_values)) - 1

        # Calculate win rate
        profitable_trades = sum(1 for trade in self.trades_history if trade['type'] == 'sell' 
                              and trade['value'] > trade['shares'] * self._find_buy_price(trade))
        total_trades = sum(1 for trade in self.trades_history if trade['type'] == 'sell')
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_value': portfolio_values[-1],
            'total_return': total_return,
            'total_return_pct': f"{total_return * 100:.2f}%",
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': f"{max_drawdown * 100:.2f}%",
            'win_rate': f"{win_rate * 100:.2f}%",
            'trades_count': len(self.trades_history),
            'portfolio_history': {
                'dates': results['dates'],
                'values': results['portfolio_value'],
                'cash': results['cash']
            },
            'trades': self.trades_history
        }

    def _find_buy_price(self, sell_trade: Dict) -> float:
        """Find the corresponding buy price for a sell trade"""
        for trade in self.trades_history:
            if (trade['type'] == 'buy' and 
                trade['symbol'] == sell_trade['symbol'] and 
                trade['date'] < sell_trade['date']):
                return trade['price']
        return 0.0