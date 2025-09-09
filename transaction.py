import pandas as pd

def calculate_capital_flow_kpis(df: pd.DataFrame):
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['type'] = df['type'].astype(str).str.strip().str.upper()

    total_invested = df.loc[df['type'] == 'BUY', 'trade_val'].sum()
    total_withdrawn = df.loc[df['type'] == 'SELL', 'trade_val'].sum()
    net_investment = total_invested - total_withdrawn

    # Calculate months in range
    if not df.empty:
        months = ((df['date'].max().year - df['date'].min().year) * 12 +
                  (df['date'].max().month - df['date'].min().month) + 1)
    else:
        months = 0

    avg_monthly = net_investment / months if months > 0 else 0
    largest_buy = df.loc[df['type'] == 'BUY', 'trade_val'].max()

    return {
        "total_invested": round(total_invested, 2),
        "total_withdrawn": round(total_withdrawn, 2),
        "net_investment": round(net_investment, 2),
        "avg_monthly_investment": round(avg_monthly, 2),
        "largest_single_investment": round(largest_buy, 2) if pd.notna(largest_buy) else 0
    }