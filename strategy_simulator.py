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
        
    def simulate(self, hist_data: pd.DataFrame, sentiment_data: pd.DataFrame) -> Dict:
        """
        Simulate investment strategy using historical price and sentiment data
        """
        results = {
            'portfolio_value': [],
            'cash': [],
            'trades': [],
            'dates': []
        }
        
        # Combine price and sentiment data
        merged_data = self._prepare_data(hist_data, sentiment_data)
        
        # Initialize simulation
        self.cash = self.initial_capital
        self.positions = {}
        
        for date, row in merged_data.iterrows():
            # Generate trading signals
            signal = self._generate_signal(row)
            
            # Execute trades based on signals
            if signal > 0 and self.cash > 0:  # Buy signal
                shares = (self.cash * 0.3) / row['Close']  # Invest 30% of cash
                self._execute_trade(row['symbol'], shares, row['Close'], date, 'buy')
            elif signal < 0 and row['symbol'] in self.positions:  # Sell signal
                self._execute_trade(row['symbol'], self.positions[row['symbol']], 
                                 row['Close'], date, 'sell')
            
            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(merged_data.loc[date])
            
            # Store results
            results['portfolio_value'].append(portfolio_value)
            results['cash'].append(self.cash)
            results['dates'].append(date)
            
        return self._calculate_metrics(results)
    
    def _prepare_data(self, hist_data: pd.DataFrame, sentiment_data: pd.DataFrame) -> pd.DataFrame:
        """Merge price and sentiment data"""
        hist_data = hist_data.copy()
        sentiment_data = sentiment_data.copy()
        
        # Ensure datetime index
        hist_data.index = pd.to_datetime(hist_data.index)
        sentiment_data['Timestamp'] = pd.to_datetime(sentiment_data['Timestamp'])
        sentiment_data.set_index('Timestamp', inplace=True)
        
        # Merge data
        merged = hist_data.join(sentiment_data[['Sentiment', 'Cumulative Sentiment']], how='left')
        merged['Sentiment'].fillna(method='ffill', inplace=True)
        merged['Cumulative Sentiment'].fillna(method='ffill', inplace=True)
        
        return merged
    
    def _generate_signal(self, data: pd.Series) -> float:
        """
        Generate trading signal based on price and sentiment
        Returns: float between -1 (strong sell) and 1 (strong buy)
        """
        signal = 0.0
        
        # Price-based signals
        if 'SMA_20' in data and 'SMA_50' in data:
            # Moving average crossover
            if data['SMA_20'] > data['SMA_50']:
                signal += 0.3
            else:
                signal -= 0.3
        
        # Sentiment-based signals
        if 'Sentiment' in data:
            # Current sentiment
            signal += data['Sentiment'] * 0.3
            
            # Sentiment trend
            if 'Cumulative Sentiment' in data:
                signal += data['Cumulative Sentiment'] * 0.4
        
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
        """Calculate performance metrics"""
        portfolio_values = np.array(results['portfolio_value'])
        
        # Calculate returns
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # Calculate metrics
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital
        sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns) if len(returns) > 0 else 0
        max_drawdown = np.min(portfolio_values / np.maximum.accumulate(portfolio_values)) - 1
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': portfolio_values[-1],
            'total_return': total_return,
            'total_return_pct': f"{total_return * 100:.2f}%",
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': f"{max_drawdown * 100:.2f}%",
            'trades_count': len(self.trades_history),
            'portfolio_history': {
                'dates': results['dates'],
                'values': results['portfolio_value'],
                'cash': results['cash']
            },
            'trades': self.trades_history
        }
