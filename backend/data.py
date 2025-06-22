import pandas as pd
import numpy as np
from datetime import datetime

def generate_historical_data():
    """Generate historical data for Wynn Resort"""
    # Create datetime range
    dates = pd.date_range(end=datetime.now(), periods=180*24, freq='h')
    df = pd.DataFrame({'datetime': dates})

    # Extract time features
    df['hour'] = df.datetime.dt.hour
    df['day'] = df.datetime.dt.dayofweek
    df['weekend'] = (df.day >= 4).astype(float)

    # Rooms 0-100 -- 85% weekend avg, 70% weekday avg, peaks at night
    df['rooms'] = np.where(df.weekend, 
                            85 + 10 * np.sin(2 * np.pi * df.hour / 24),
                            70 + 15 * np.sin(2 * np.pi * df.hour / 24))

    # Cleaning 0-160+ -- Peaks 10am-2pm (checkout) and 6-8pm (turndown)
    df['cleaning'] = np.where((df.hour >= 10) & (df.hour <= 14), 
                                80 + df.rooms * 0.8,
                                np.where((df.hour >= 18) & (df.hour <= 20),
                                        40 + df.rooms * 0.3,
                                        20 + df.rooms * 0.1))

    # Security 0-75 -- Higher at night (10pm-4am), extra on weekends
    df['security'] = np.where((df.hour >= 22) | (df.hour <= 4),
                                40 + df.weekend * 20 + 10,
                                20 + df.weekend * 10 + 5)

    # Add noise
    df['rooms'] = np.clip(df.rooms + np.random.normal(0, 5, len(df)), 0, 100)
    df['cleaning'] = np.clip(df.cleaning + np.random.normal(0, 10, len(df)), 0, None)
    df['security'] = np.clip(df.security + np.random.normal(0, 5, len(df)), 0, None)
    
    return df[['datetime', 'rooms', 'cleaning', 'security']]

def prepare_features(df):
    """Prepare features for model training"""
    df = df.copy()
    df['hour_norm'] = df.datetime.dt.hour / 24
    df['day_norm'] = df.datetime.dt.dayofweek / 6
    df['hour_sin'] = np.sin(2 * np.pi * df.datetime.dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df.datetime.dt.hour / 24)
    df['weekend'] = (df.datetime.dt.dayofweek >= 5).astype(float)
    
    features = ['hour_norm', 'day_norm', 'hour_sin', 'hour_cos', 'weekend']
    targets = ['rooms', 'cleaning', 'security']
    
    return df, features, targets

def create_sequences(X, y, seq_len=24):
    """Create sequences for LSTM training"""
    X_seq = np.array([X[i:i+seq_len] for i in range(len(X)-seq_len)])
    y_seq = np.array([y[i:i+seq_len] for i in range(len(y)-seq_len)])
    return X_seq, y_seq