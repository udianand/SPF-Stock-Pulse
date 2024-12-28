import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import Tuple, Dict

class StockPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and target for prediction
        """
        # Create features
        df_features = df[self.feature_columns].copy()
        
        # Add technical indicators
        df_features['SMA_5'] = df['Close'].rolling(window=5).mean()
        df_features['SMA_20'] = df['Close'].rolling(window=20).mean()
        df_features['RSI'] = self._calculate_rsi(df['Close'])
        df_features['Price_Change'] = df['Close'].pct_change()
        df_features['Volume_Change'] = df['Volume'].pct_change()
        
        # Create target (next day's closing price)
        target = df['Close'].shift(-1)
        
        # Drop rows with NaN values
        df_features = df_features.dropna()
        target = target[df_features.index]
        
        return df_features, target
        
    def train(self, hist_data: pd.DataFrame) -> Dict:
        """
        Train the prediction model
        """
        # Prepare data
        features, target = self.prepare_data(hist_data)
        
        # Remove last row (no target available)
        features = features[:-1]
        target = target[:-1]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate metrics
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'feature_importance': dict(zip(features.columns, self.model.feature_importances_))
        }
    
    def predict_next_day(self, hist_data: pd.DataFrame) -> Dict:
        """
        Predict the next day's closing price
        """
        # Prepare features
        features, _ = self.prepare_data(hist_data)
        
        # Get the last available data point
        last_data = features.iloc[-1:]
        
        # Scale the features
        last_data_scaled = self.scaler.transform(last_data)
        
        # Make prediction
        prediction = self.model.predict(last_data_scaled)[0]
        current_price = hist_data['Close'].iloc[-1]
        price_change = ((prediction - current_price) / current_price) * 100
        
        return {
            'current_price': current_price,
            'predicted_price': prediction,
            'predicted_change_percent': price_change
        }
    
    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
