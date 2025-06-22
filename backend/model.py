import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from data import generate_historical_data, prepare_features, create_sequences

logger = logging.getLogger(__name__)

class ForecastModel:
    """LSTM model for Wynn Resort forecasting"""
    def __init__(self):
        self.model = None
        self.X_mean = None
        self.X_std = None
        self.y_mean = None
        self.y_std = None
        self.features = None
        self.seq_len = 24
        
        # Train model on initialization
        self._train_model()
        
    def _preprocess_data(self):
        """Preprocess data for model training"""
        # Generate historical data
        historical_data = generate_historical_data()
        
        # Prepare features
        df, features, targets = prepare_features(historical_data)
        self.features = features
        
        # Extract arrays
        X = df[features].values
        y = df[targets].values
        
        # Create sequences
        X_seq, y_seq = create_sequences(X, y, self.seq_len)
        
        # Normalize
        self.X_mean, self.X_std = X_seq.mean(), X_seq.std()
        self.y_mean, self.y_std = y_seq.mean(), y_seq.std()
        X_seq_norm = (X_seq - self.X_mean) / self.X_std
        y_seq_norm = (y_seq - self.y_mean) / self.y_std
        
        # Split - last 168 hours for validation
        val_seqs = 145
        X_train, X_val = X_seq_norm[:-val_seqs], X_seq_norm[-val_seqs:]
        y_train, y_val = y_seq_norm[:-val_seqs], y_seq_norm[-val_seqs:]
        
        return X_train, X_val, y_train, y_val
        
    def _train_model(self):
        """Train the LSTM model"""
        logger.info("Training forecast model...")
        
        # Preprocess data
        X_train, X_val, y_train, y_val = self._preprocess_data()
        
        # Build and train model
        self.model = Sequential([
            LSTM(20, return_sequences=True),
            Dense(3)
        ])
        self.model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
        
        early_stop = EarlyStopping(monitor='accuracy', baseline=0.95)
        self.model.fit(X_train, y_train, validation_data=(X_val, y_val), 
                      epochs=50, verbose=0, callbacks=[early_stop])
        
        logger.info("Model training complete!")
        
    def generate_forecast(self, hours=168):
        """Generate forecast for the next N hours"""
        # Get recent historical data
        historical_data = generate_historical_data()
        df, _, _ = prepare_features(historical_data)
        
        predictions = []
        current = df.tail(24).copy()
        
        # Generate 7 days of predictions
        for day in range(hours // 24):
            # Normalize and predict
            X_norm = (current[self.features].values - self.X_mean) / self.X_std
            pred = self.model.predict(X_norm[None, :, :], verbose=0)[0] * self.y_std + self.y_mean
            
            # Store predictions with timestamps
            start = current.iloc[-1]['datetime']
            for i in range(24):
                t = start + timedelta(hours=i+1)
                predictions.append({
                    'datetime': t,
                    'date': t.isoformat(),
                    'rooms': float(np.clip(pred[i,0], 0, 100)),
                    'cleaning': int(max(0, pred[i,1])),
                    'security': int(max(0, pred[i,2]))
                })
            
            # Next 24 hours features
            times = pd.date_range(start + timedelta(hours=1), periods=24, freq='h')
            current = pd.DataFrame({
                'datetime': times,
                'hour_norm': times.hour / 24,
                'day_norm': times.dayofweek / 6,
                'hour_sin': np.sin(2 * np.pi * times.hour / 24),
                'hour_cos': np.cos(2 * np.pi * times.hour / 24),
                'weekend': (times.dayofweek >= 5) * 1.0
            })
        
        return predictions[:hours]
    
    def generate_historical(self, hours=168):
        """Generate historical data for context"""
        historical_data = generate_historical_data()
        
        # Get last N hours
        recent = historical_data.tail(hours)
        
        # Convert to expected format
        historical = []
        for _, row in recent.iterrows():
            historical.append({
                'datetime': row['datetime'],
                'date': row['datetime'].isoformat(),
                'rooms': float(row['rooms']),
                'cleaning': int(row['cleaning']),
                'security': int(row['security'])
            })
            
        return historical