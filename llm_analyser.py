from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage
import pandas as pd
from openai import OpenAI

def analyze_mutual_funds_with_llama(df: pd.DataFrame, investment_amount: float) -> str:
    """
    Uses LLaMA 3 via Ollama to analyze mutual fund metrics and suggest investment allocation.

    Parameters:
        df (pd.DataFrame): DataFrame containing mutual fund metrics.
        investment_amount (float): Total amount to be invested.

    Returns:
        str: Plain text explanation and recommendation.
    """
    print("🤖 Analyzing mutual fund data with LLaMA 3...")

    llm = ChatOllama(model="llama3")

    df_text = df.to_string(index=False)

    prompt = f"""
You are an expert financial analyst.

Your task is to thoroughly analyze each mutual fund listed in the table below. Go through every fund independently and objectively.

For each fund:
- Evaluate its investment worthiness based solely on the data provided.
- Be honest, specific, and unbiased in your assessment.
- Clearly state whether the fund is **Strong**, **Average**, or **Weak** overall.

Then provide:
**1. Analysis with Strengths and Weaknesses of Each Fund:**  
List each fund separately with bullet points under **Strengths** and **Weaknesses**.

**2. Recommendation Section:**  
Indicate which fund(s) are best suited for different types of investors (e.g., conservative, aggressive). Only include worthy funds here.

**3. Confidence Score and Ranking:**  
Give a score out of 100 for each recommended fund.  
- List them in order of confidence.  
- Format as bullet points.

**4. Suggested Allocation of ₹{investment_amount}:**  
Allocate funds only to the top 3 ranked options.  
- Show allocation in bullet points.
- If any funds are not investable, say so clearly.

Use **bold section headers** and ensure the final output is clean and easy to read.  
Do not include any explanation or extra text outside the 4 required sections.

Data:
---
{df_text}
---
"""


    messages = [
        SystemMessage(content="You are a helpful and brutally honest financial advisor."),
        HumanMessage(content=prompt)
    ]

    response = llm.invoke(messages)
    return response.content.strip()



  # Automatically reads OPENAI_API_KEY from environment

def analyze_mutual_funds_with_gpt(df: pd.DataFrame, investment_amount: float, model: str = "gpt-3.5-turbo") -> str:
    """
    Uses GPT-4o or GPT-4 Turbo to analyze mutual fund metrics and suggest investment allocation.

    Parameters:
        df (pd.DataFrame): DataFrame containing mutual fund metrics.
        investment_amount (float): Total amount to be invested.
        model (str): OpenAI model to use, e.g., "gpt-4o" or "gpt-4-turbo".

    Returns:
        str: Plain text explanation and recommendation.
    """
    client = OpenAI()
    print(f"🤖 Analyzing mutual fund data with {model}...")

    df_text = df.to_string(index=False)

    prompt = f"""
You are an expert financial analyst.

Your task is to thoroughly analyze each mutual fund listed in the table below. Go through every fund independently and objectively.

For each fund:
- Evaluate its investment worthiness based solely on the data provided.
- Be honest, specific, and unbiased in your assessment.
- Clearly state whether the fund is **Strong**, **Average**, or **Weak** overall.

Then provide:
**1. Analysis with Strengths and Weaknesses of Each Fund:**  
List each fund separately with bullet points under **Strengths** and **Weaknesses**.

**2. Recommendation Section:**  
Indicate which fund(s) are best suited for different types of investors (e.g., conservative, aggressive). Only include worthy funds here.

**3. Confidence Score and Ranking:**  
Give a score out of 100 for each recommended fund.  
- List them in order of confidence for all the funds.  
- Format as bullet points.

**4. Suggested Allocation of ₹{investment_amount}:**  
Allocate funds only to the top 3 ranked options.  
- Show allocation in bullet points.
- If any funds are not investable, say so clearly.

Use **bold section headers** and ensure the final output is clean and easy to read.  
Do not include any explanation or extra text outside the 4 required sections.

Data:
---
{df_text}
---
"""

    chat_response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful and brutally honest financial advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return chat_response.choices[0].message.content.strip()




def analyze_mutual_funds_portfolio_with_gpt(
    df: pd.DataFrame,
    investment_amount: float,
    future_investment: float,
    investment_df: pd.DataFrame = None,
    category: str = None,
    model: str = "gpt-4-turbo"
) -> str:
    """
    Analyzes mutual fund data using GPT to suggest an investment strategy.

    Parameters:
        df (pd.DataFrame): Mutual fund metrics (e.g., returns, ratios).
        investment_amount (float): Amount planned to invest now (lumpsum).
        investment_df (pd.DataFrame, optional): Current holdings with 'Scheme Name' and 'Market Value'.
        model (str): GPT model to use.

    Returns:
        str: GPT analysis and recommendations.
    """
    # Assuming your data is in a DataFrame called df
    rows_to_remove = [
    'Riskometer',
    'Exit Load (Days)',
    '1 Day',
    '1 Week',
    'Commodities',
    'Category',
    'index_x',
    'index_y'
]


    df = df[~df['Metric'].isin(rows_to_remove)]


    client = OpenAI()
    print(f"🤖 Analyzing mutual fund data with {model}...")

    df_text = df.to_string(index=False)

    investment_text = ""
    if investment_df is not None and not investment_df.empty:
        investment_text = "\nCurrent Holdings:\n" + investment_df.to_string(index=False)

    prompt = f"""
You are a highly experienced financial analyst and mutual fund advisor.

Your task is to analyze the mutual funds provided in the dataset below and identify the most suitable options for **investment today**.

### Evaluate Each Fund:
- Focus on long-term performance (3Y, 5Y, 7Y) for **growth potential**
- Use short-term metrics (1Y, 6M, 3M) for **momentum and recent consistency**
- Consider **risk-adjusted returns** using Sharpe, Sortino, Std Dev
- Factor in Alpha, Expense Ratio, Turnover, AUM (Net Assets), and Sector concentration
- Classify each fund as:
  🔹 **Strong** – Suitable for fresh investment  
  🔸 **Average** – Decent, may be held but not preferred  
  🔻 **Weak** – Not suitable for new investment

---

### Scoring framework (make ranking explainable and consistent):
- Build a 0–100 composite score using normalized ranks across funds (higher is better). Use this weighting:
  - Long-term performance (3Y/5Y/7Y): 40% (equal-weight or availability-weighted)
  - Short-term momentum (1Y=50%, 6M=30%, 3M=20%): 25%
  - Risk-adjusted (Sharpe 50%, Sortino 30%, lower Std Dev 20%): 20% (invert Std Dev)
  - Alpha: 10% (higher better)
  - Cost & efficiency (lower Expense Ratio 70%, lower Turnover 30%): 5% (invert both)
- If a metric is missing (e.g., 7Y for a new fund), re-weight the available metrics proportionally and clearly flag the omission.
- For each fund, after the score and classification badge, include a **compact reasoning block** in `<small>` tags:
  - Show metric-by-metric contribution, e.g., “LT avg rank 85/100 → 34 pts; ST momentum rank 70/100 → 17.5 pts; Risk-adj rank 90/100 → 18 pts; Alpha 5/10 pts; Cost 3.5/5 pts”
  - List any penalties/bonuses applied, e.g., “AUM < ₹1,000 Cr: -2 pts; Sector top 3 = 57%: -1.5 pts”
  - Show the final composite sum, e.g., “Final = 34 + 17.5 + 18 + 5 + 3.5 – 3.5 = 74.5”
  - Keep ≤4 lines per fund, factual language, inside `<small>`.

---

### Guardrails & tie-breakers:
- Prefer funds with **AUM ≥ ₹1,000 Cr** for liquidity and stability (if available). If lower, allow only with strong scores and add a caution note.
- Penalize excessive concentration: if Top 3 sectors > 55% or Top 10 stocks > 50%, apply a small score haircut and note it.
- If two funds tie (±1 point), break ties by: higher Sharpe > lower Expense > higher Alpha > lower Std Dev.

---

### Points to consider:
- Newer funds must be evaluated equally based on available performance and fundamentals; do not auto-penalize age.
- If a fund has strong fundamentals but lacks recent performance, **avoid** recommending it.
- Favor funds with consistent short-term momentum **and** solid long-term strength.
- Use only the data provided; do not fabricate or infer unavailable values. If data is missing, write “Not available”.

---

### Presentation rules (make it clean, executive-ready):
- Output must be clean HTML wrapped in <div class='llm-analysis'>...</div> only (no markdown).
- Use these elements only: <div>, <h3>, <h4>, <ul>, <li>, <br>, <strong>, <em>, <small>, <span>, <hr>, <table>, <thead>, <tbody>, <tr>, <th>, <td>.
- Add a compact top summary with **three KPI cards** (inline boxes):
  - Funds analyzed, Top picks (count), Total Buy = ₹{investment_amount}
- Use **badges** for classifications and actions:
  - Strong: <span style="background:#16a34a;color:#fff;padding:2px 6px;border-radius:6px;">Strong</span>
  - Average: <span style="background:#f59e0b;color:#111;padding:2px 6px;border-radius:6px;">Average</span>
  - Weak: <span style="background:#dc2626;color:#fff;padding:2px 6px;border-radius:6px;">Weak</span>
  - Actions Buy/Sell/Exit/Hold use color pills (Buy #16a34a, Sell #dc2626, Exit #9333ea, Hold #64748b)
- Number formatting:
  - Rupee amounts in Indian format (e.g., ₹1,23,45,678)
  - Percentages to 2 decimals (e.g., 12.34%)
  - Color-code returns inline: positive green (#16a34a), negative red (#dc2626)
- Tables:
  - Full width, compact: <table style="width:100%;border-collapse:collapse;">
  - <th>/<td> style: border:1px solid #e5e7eb; padding:8px; text-align:left
  - Include a **Totals** row at the bottom for Target Value and Buy/Sell amounts
- Insert thin separators using <hr style="border:none;border-top:1px solid #e5e7eb;margin:12px 0;">
- Add a tiny legend at the end using <small> to explain color badges

---

### Sections to generate:

<h3>1. Summary of Fund Analysis:</h3>
- Keep it under 200 words
- Bullet points only
- Pinpoint key insights, sector skews, outliers, trends

<h3>2. Confidence Score and Ranking:</h3>
- For each fund, list in strictly descending order of composite score (highest first — no ties out of order).
- Show the fund name, score out of 100, and classification badge.
- After the score, provide a single, concise headline reason summarising the top 2–3 drivers of that score.
- On the next line, in <small> tags, add any short cautionary note or single‑line context (e.g., missing metric, AUM caution, sector concentration), but do NOT include metric‑by‑metric breakdowns or numeric contribution steps.
- Keep each fund’s entry compact — maximum 2 lines (headline + <small>).

<h3>3. Suggested Allocation of ₹{investment_amount}:</h3>
- Allocate to top 3 ranked funds only (show % and ₹)
- Use badges for fund classification
- Clearly list **funds to avoid** with one-line reasons
- Cap any single fund at 50% of allocation unless noted

---

### Optional post-trade checks (include if data available):
- “Post-Trade Sector Exposure” note if any sector exceeds 35–40% after allocation
- <small>Assumptions & Limitations</small> with data as-of date and exclusions

✅ SAY:
Use HTML tags exactly as specified: 
<strong>, <ul><li>, <br>, <h3>/<h4>, <hr>, wrap all in <div class='llm-analysis'>...</div>

Input Data:
---
{df_text}
{investment_text}
---
"""




    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful and brutally honest financial advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()




