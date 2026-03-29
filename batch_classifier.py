import pandas as pd
import os
import json
from glob import glob

def classify_stock(csv_path, stock_name):
    try:
        df = pd.read_csv(csv_path)
        df['published_date'] = pd.to_datetime(df['published_date'])
        df = df.sort_values('published_date').reset_index(drop=True)
        
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        def classify(row):
            close = row['close']
            ema_9 = row['ema_9']
            ema_50 = row['ema_50']
            
            if ema_9 > ema_50 and close < ema_9:
                return 'SELL_WAIT'
            elif ema_9 > ema_50 and close >= ema_50 and close < ema_9:
                return 'BUY'
            elif ema_9 > ema_50 and close >= ema_9:
                return 'HOLD_PROFIT'
            elif ema_9 < ema_50:
                return 'GET_LOST'
            elif (df['ema_9'].shift(1) < df['ema_50'].shift(1)).iloc[-1] and ema_9 > ema_50 and close >= ema_9 and close < ema_50:
                return 'QUICK_PROFIT'
            return 'IGNORE'
        
        latest = df.iloc[-1]
        latest['classification'] = classify(latest)
        
        return {
            'symbol': stock_name,
            'date': str(latest['published_date'].date()),
            'close': round(latest['close'], 2),
            'ema_9': round(latest['ema_9'], 2),
            'ema_50': round(latest['ema_50'], 2),
            'signal': latest['classification']
        }
    except Exception as e:
        return {'symbol': stock_name, 'error': str(e)}

# Process all CSVs
results = []
csv_files = glob('/mnt/user-data/uploads/*.csv')

for csv_file in csv_files:
    stock_name = os.path.basename(csv_file).replace('.csv', '').upper()
    result = classify_stock(csv_file, stock_name)
    results.append(result)
    print(f"✓ {stock_name}")

# Save to JSON
with open('/mnt/user-data/outputs/stocks_data.json', 'w') as f:
    json.dump(results, f, indent=2)

# Summary
df_results = pd.DataFrame(results)
print(f"\nTotal: {len(results)}")
print(f"\nSignal breakdown:")
print(df_results['signal'].value_counts())

print(f"\n✓ Exported to stocks_data.json")
