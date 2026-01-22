# csv_loader.py
import pandas as pd

def load_boss_urls(csv_path):
    """Load boss names and URLs from CSV file"""
    try:
        df = pd.read_csv(csv_path)
        return dict(zip(df['Boss_Name'], df['URL']))
    except Exception as e:
        print(f"❌ CSV Error: {e}")
        return {}