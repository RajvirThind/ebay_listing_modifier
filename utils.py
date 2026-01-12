import pandas as pd
import math

def numerate_stock(stock):
    if stock == 'Out of Stock':
        return 0
    elif stock == 'In Stock':
        return 30
    else:
        try:
            return int(float(stock))
        except Exception:
            return None

def multiply_price(price):
    try:
        # Handles strings like "10.50 GBP" by taking the first part
        new_price = float(str(price).split(' ')[0]) * 1 #edit multiplier later
        final_price = math.ceil(new_price) - 0.51
        return f"{final_price:.2f}"
    except (ValueError, TypeError, AttributeError):
        return "0.00"

def load_and_process_stock(path):
    # Load S3 file
    df = pd.read_csv(path, sep="\t")
    processed_df = df.copy()
    
    # Apply Numeration
    if 'Stock' in processed_df.columns:
        processed_df['Stock'] = processed_df['Stock'].apply(numerate_stock)
    
    # Apply Price Logic
    if 'WholeSale Price' in processed_df.columns:
        processed_df['WholeSale Price'] = processed_df['WholeSale Price'].apply(multiply_price)
    
    # Rename for eBay Join
    if 'SKU' in processed_df.columns:
        processed_df.rename(columns={'SKU': 'Custom label (SKU)'}, inplace=True)
    
    return processed_df

def filter_stock_data(path):
    df = pd.read_csv(path, sep="\t")
    processed_df = df.copy()
    
    # Apply Numeration
    if 'Stock' in processed_df.columns:
        processed_df['Stock'] = processed_df['Stock'].apply(numerate_stock)

    return processed_df
