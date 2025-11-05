from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import json

app = Flask(__name__)

# Generate sample transaction data
def generate_sample_data(user_id, pattern='normal'):
    transactions = []
    base_date = datetime(2025, 1, 1)
    
    if pattern == 'normal':
        # Normal spending pattern
        for i in range(60):
            transactions.append({
                'id': f'txn_{i}',
                'user_id': user_id,
                'amount': np.random.uniform(50, 800),
                'date': (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                'type': np.random.choice(['deposit', 'withdrawal', 'transfer']),
                'description': np.random.choice(['Grocery', 'Rent', 'Salary', 'Shopping', 'Utilities'])
            })
    
    elif pattern == 'structuring':
        # Structuring pattern - multiple transactions just below $10k
        for i in range(60):
            if i % 4 == 0:
                amount = np.random.uniform(9200, 9800)
            else:
                amount = np.random.uniform(50, 500)
            
            transactions.append({
                'id': f'txn_{i}',
                'user_id': user_id,
                'amount': amount,
                'date': (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                'type': np.random.choice(['deposit', 'withdrawal', 'transfer']),
                'description': 'Transaction'
            })
    
    elif pattern == 'rapid':
        # Rapid movement pattern
        for i in range(100):
            transactions.append({
                'id': f'txn_{i}',
                'user_id': user_id,
                'amount': np.random.uniform(1000, 5000),
                'date': (base_date + timedelta(days=i//3)).strftime('%Y-%m-%d'),
                'type': np.random.choice(['deposit', 'withdrawal']),
                'description': 'Quick Transfer'
            })
    
    return transactions

# Feature engineering for ML model
def extract_features(transactions_df):
    features = {}
    
    # Amount-based features
    features['avg_amount'] = transactions_df['amount'].mean()
    features['std_amount'] = transactions_df['amount'].std()
    features['max_amount'] = transactions_df['amount'].max()
    features['min_amount'] = transactions_df['amount'].min()
    
    # Count near threshold (e.g., $9,000-$10,000)
    features['near_threshold_count'] = len(transactions_df[
        (transactions_df['amount'] >= 9000) & (transactions_df['amount'] < 10000)
    ])
    
    # Transaction frequency
    features['total_transactions'] = len(transactions_df)
    features['transactions_per_day'] = len(transactions_df) / transactions_df['date'].nunique()
    
    # Round number transactions (ending in 00)
    features['round_number_ratio'] = len(
        transactions_df[transactions_df['amount'] % 100 == 0]
    ) / len(transactions_df)
    
    # Velocity - rapid movement
    features['velocity_score'] = features['transactions_per_day'] * features['avg_amount'] / 1000
    
    return features

# Simple rule-based detection
def detect_suspicious_activity(features):
    risk_score = 0
    flags = []
    
    # Check for structuring
    if features['near_threshold_count'] > 5:
        risk_score += 40
        flags.append('Structuring: Multiple transactions near $10k threshold')
    
    # Check for high velocity
    if features['transactions_per_day'] > 3:
        risk_score += 25
        flags.append('High Velocity: Unusually high transaction frequency')
    
    # Check for round numbers
    if features['round_number_ratio'] > 0.5:
        risk_score += 20
        flags.append('Round Numbers: High percentage of exact amount transactions')
    
    # Check for large amounts
    if features['avg_amount'] > 5000:
        risk_score += 15
        flags.append('Large Amounts: Average transaction significantly above normal')
    
    # Determine risk level
    if risk_score >= 60:
        risk_level = 'HIGH'
    elif risk_score >= 30:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return {
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'flags': flags
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users')
def get_users():
    users = [
        {'id': 'user_001', 'name': 'John Doe (Normal)', 'pattern': 'normal'},
        {'id': 'user_002', 'name': 'Jane Smith (Structuring)', 'pattern': 'structuring'},
        {'id': 'user_003', 'name': 'Bob Johnson (Rapid)', 'pattern': 'rapid'}
    ]
    return jsonify(users)

@app.route('/api/analyze/<user_id>')
def analyze_user(user_id):
    # Get pattern from query parameter
    pattern = request.args.get('pattern', 'normal')
    
    # Generate transactions
    transactions = generate_sample_data(user_id, pattern)
    df = pd.DataFrame(transactions)
    
    # Extract features
    features = extract_features(df)
    
    # Detect suspicious activity
    detection_result = detect_suspicious_activity(features)
    
    # Prepare daily aggregation for chart
    df['date'] = pd.to_datetime(df['date'])
    daily_spending = df.groupby('date').agg({
        'amount': 'sum',
        'id': 'count'
    }).reset_index()
    daily_spending.columns = ['date', 'total_amount', 'transaction_count']
    daily_spending['date'] = daily_spending['date'].dt.strftime('%Y-%m-%d')
    
    # Category breakdown
    category_spending = df.groupby('type')['amount'].sum().reset_index()
    category_spending.columns = ['category', 'amount']
    
    return jsonify({
        'user_id': user_id,
        'transactions': transactions[:20],  # Last 20 for display
        'features': features,
        'detection': detection_result,
        'charts': {
            'daily_spending': daily_spending.to_dict('records'),
            'category_breakdown': category_spending.to_dict('records'),
            'amount_distribution': df['amount'].tolist()
        }
    })

if __name__ == '__main__':
    app.run(debug=True)