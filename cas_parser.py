import os
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader
from pypdf import PdfReader, PdfWriter
import pandas as pd
from io import StringIO
import re
import json
import pdfplumber

from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage

# Load API key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def remove_pdf_password(input_path: str, password: str) -> str:
    print(f"🔓 Removing password from PDF...")
    try:
        # Prepare output file path in same folder
        base_dir = os.path.dirname(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(base_dir, f"{base_name}_decrypted.pdf")

        reader = PdfReader(input_path)

        if reader.is_encrypted:
            if not reader.decrypt(password):
                return "❌ Incorrect password. Cannot decrypt PDF."

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"✅ Password removed successfully. Saved to {output_path}")
        return output_path

    except Exception as e:
        return f"❌ Error: {str(e)}"

def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def ask_gpt_for_portfolio_table(pdf_text: str, model = "gpt-4") -> str:
    print(f"📄 Extracting mutual fund portfolio table using {model}...")
    prompt = (
        "The following is the extracted text from a Consolidated Account Statement (CAS) "
        "of mutual funds. Extract and format the mutual fund portfolio in a table format "
        "with these columns: Folio No, Scheme Name, Unit Balance, NAV, NAV Date, Registrar, ISIN, Cost Value, Market Value.\n\n"
        f"Text:\n{pdf_text}\n\n"
        "Return only the table."
    )

    response = client.chat.completions.create(
        model=model,
        # model = "gpt-4-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content



def extract_portfolio_table_from_cas(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = text.splitlines()
    portfolio = []

    # Regex pattern for one-line portfolio entries
    pattern = re.compile(
        r"(\d{7,12}.\d{1,3}|\d{8})\s?+(INF\w{9})\s+(.*?)\s?-?\s?+([\d,]+\.\d{3})\s+([\d,]+\.\d{3})\s+(\d{2}-[A-Za-z]{3}-\d{4})\s+([\d.]+)\s+([\d,]+\.\d{2})\s+(CAMS|KFINTECH)"
    )

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            folio, isin, scheme, cost, units, nav_date, nav, market_value, registrar = match.groups()
            portfolio.append({
                "Folio No": folio,
                "Scheme Name": scheme.strip(),
                "Unit Balance": float(units.replace(",", "")),
                "NAV Date": nav_date,
                "NAV": float(nav),
                "Registrar": registrar,
                "ISIN": isin,
                "Cost Value": float(cost.replace(",", "")),
                "Market Value": float(market_value.replace(",", ""))
            })
    df = pd.DataFrame(portfolio)
    return df


def ask_llama_for_portfolio_table(pdf_text: str) -> str:
    """
    Uses LLaMA 3 via Ollama to extract mutual fund portfolio table from CAS text.

    Parameters:
        pdf_text (str): Raw text extracted from the Consolidated Account Statement (CAS) PDF.

    Returns:
        str: Cleaned mutual fund portfolio in table format with specific columns.
    """
    print("📄 Extracting mutual fund portfolio table using LLaMA 3...")

    llm = ChatOllama(model="llama3")  # or llama3:70b

    prompt = f"""
You are a structured data extraction assistant.

Extract only the mutual fund portfolio table from the CAS text below.

Return the table with exactly these columns:
Folio No | Scheme Name | Unit Balance | NAV | NAV Date | Registrar | ISIN | Cost Value | Market Value

Only return the table with these columns and their values from the CAS text. Do not include any explanation or extra text.

CAS Text:
---
{pdf_text}
---
"""

    messages = [
        SystemMessage(content="You are a helpful and detail-oriented data extractor."),
        HumanMessage(content=prompt.strip())
    ]

    response = llm.invoke(messages)
    return response.content.strip()




def extract_investment_table(text: str) -> str:
    """
    Extract only the mutual fund portfolio section from a raw CAS PDF text.
    
    Starts after the 'Market ValueFolio No.' header and ends before 'Total' or footer code.

    Parameters:
        text (str): Full raw CAS text.

    Returns:
        str: Trimmed portfolio section text.
    """
    lines = text.strip().splitlines()
    start_idx = -1
    end_idx = -1

    # Step 1: Find starting line index
    for i, line in enumerate(lines):
        if "Market ValueFolio No" in line:
            start_idx = i
            break

    if start_idx == -1:
        raise ValueError("Portfolio section header not found.")

    # Step 2: Find ending line index
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip().startswith("Total") or "CASWS" in lines[i]:
            end_idx = i
            break

    if end_idx == -1:
        end_idx = len(lines)  # fallback: take everything till end

    # Step 3: Extract block
    portfolio_lines = lines[start_idx:end_idx]
    portfolio_lines = "\n".join(portfolio_lines)
    print(portfolio_lines)
    return portfolio_lines



def clean_portfolio_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Remove commas and convert to float
    for col in ["Unit Balance", "Cost Value", "Market Value"]:
        df[col] = df[col].str.replace(",", "").astype(float)

    # Convert NAV if not already float
    if df["NAV"].dtype != float:
        df["NAV"] = df["NAV"].astype(float)

    # Convert NAV Date to datetime
    df["NAV Date"] = pd.to_datetime(df["NAV Date"], format="%d-%b-%Y")

    # Ensure other columns are strings
    for col in ["Scheme Name", "Registrar", "ISIN", "Folio No"]:
        df[col] = df[col].astype(str).str.strip()

    return df


def markdown_table_to_dataframe(table_str: str) -> pd.DataFrame:
    # Remove leading/trailing spaces and clean up repeated header lines if needed
    lines = table_str.strip().split('\n')

    # Filter out separator line (with dashes)
    lines = [line for line in lines if not set(line.strip()) <= {'|', '-', ' '}]

    # Join cleaned lines into CSV-like format
    clean_table = '\n'.join(lines)
    
    # Convert to DataFrame
    df = pd.read_csv(StringIO(clean_table), sep='|', engine='python')
    
    # Remove unnamed columns from empty edges (if any)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    
    # Strip spaces
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    
    # Clean the DataFrame
    df = clean_portfolio_dataframe(df)
    df["Scheme Name"] = df["Scheme Name"].str.replace(r"^[\w\s]+ -\s*", "", regex=True)
    df["Scheme Name"] = df["Scheme Name"].str.replace(r"\s*\(.*?\)", "", regex=True)
    print(df.head()) 
    return df

# Add Market Cap column based on Scheme Name content
def get_market_cap(name):
    name_lower = name.lower()
    if 'small' in name_lower:
        return 'Small Cap'
    elif 'mid' in name_lower:
        return 'Mid Cap'
    elif 'large' in name_lower or 'bharat 22' in name_lower:
        return 'Large Cap'
    elif 'infra' in name_lower or 'infrastructure' in name_lower or 'build' in name_lower:
        return 'Infrastructure'
    elif 'tax' in name_lower or 'elss' in name_lower:
        return 'Tax Saving'
    elif 'gold' in name_lower:
        return 'Gold'
    elif 'psu' in name_lower:
        return 'PSU'
    else:
        return 'Other'



def get_clean_scheme_market_value(df: pd.DataFrame, json_path: str) -> pd.DataFrame:
    """
    Returns a new DataFrame with cleaned scheme names and their corresponding market value.

    Args:
        df (pd.DataFrame): Original DataFrame containing mutual fund data.
        json_path (str): Path to JSON file that maps old scheme names to new ones.

    Returns:
        pd.DataFrame: New DataFrame with 'Scheme Name' and 'Market Value'.
    """
    # Load scheme name mapping
    with open(json_path, 'r') as f:
        scheme_name_map = json.load(f)

    # Replace scheme names
    df = df.copy()  # to avoid modifying original
    df["Scheme Name"] = df["Scheme Name"].replace(scheme_name_map)

    # Create and clean the required DataFrame
    result_df = df[["Scheme Name", "Market Value"]].copy()
    result_df["Market Value"] = pd.to_numeric(result_df["Market Value"], errors="coerce")

    # Optional: drop rows with NaN Market Value
    result_df.dropna(subset=["Market Value"], inplace=True)
    result_df.reset_index(drop=True, inplace=True)

    return result_df

def merge_portfolios(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    # Combine both dataframes
    combined_df = pd.concat([df1, df2], ignore_index=True)

    # Group by ISIN and preserve metadata from the first occurrence
    merged_df = combined_df.groupby('ISIN', as_index=False).agg({
        'Folio No': 'first',   # Keep one folio number
        'Scheme Name': 'first',
        'Unit Balance': 'sum',
        'NAV': 'first',
        'Cost Value': 'sum',
        'Market Value': 'sum',
        'NAV Date': 'first',
        'Registrar': 'first',
        'Market Cap': 'first'
    })

    # ✅ Round numeric columns to 2 decimal places
    round_cols = ['Unit Balance', 'NAV', 'Cost Value', 'Market Value']
    merged_df[round_cols] = merged_df[round_cols].round(2)

    # Optional: sort by Market Value descending
    merged_df = merged_df.sort_values(by='Market Value', ascending=False)

    return merged_df



