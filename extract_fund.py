
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
import pandas as pd
import os
from pandas import concat



def select_fund(driver, wait, fund_name, index=0):
    """
    Fills the specified fund search box with the given fund name and selects the matched suggestion.

    Args:
        driver: Selenium WebDriver instance.
        wait: WebDriverWait instance.
        fund_name: Name of the fund to search.
        index: Index (0-4) for the respective fund search input box.
    """
    try:
        # Determine correct input box ID
        input_id = "peer-fund-search" if index == 0 else f"peer-fund-search{index+1}"
        fund_input = wait.until(EC.presence_of_element_located((By.ID, input_id)))

        fund_input.click()

        time.sleep(0.5)
        fund_input.clear()

        # Force clear any previous value
        fund_input.send_keys(Keys.CONTROL + "a")
        fund_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.5)

        # print("inside select fun", fund_name)

        fund_input.send_keys(fund_name)
        print(f"🔍 Searching for: {fund_name} in #{input_id}")
        time.sleep(5)


        # Normalize function to reduce false matches
        def normalize(text):
            return (
                text.lower()
                .replace("direct", "dir")
                .replace("&", "and")
                .replace("  ", " ")
                .strip()
            )

        # Wait for suggestions
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".tt-dataset-fund_search .tt-suggestion")))
        

        # Get all suggestions
        suggestions = driver.find_elements(By.CSS_SELECTOR, ".tt-dataset-fund_search .tt-suggestion")

        target = normalize(fund_name)
        found = False

        for suggestion in suggestions:
            suggestion_text = normalize(suggestion.text)
            # print(f"Checking suggestion: {suggestion_text} against target: {target}")
            
            if suggestion_text == target:
                suggestion.click()
                print(f"✅ Exactly matched and selected: {suggestion.text.strip()}")
                found = True
                break
            else:
                driver.execute_script("document.body.click();")

        if not found:
            print(f"❌ Exact match not found for: {fund_name}")


    except Exception as e:
        print(f"❌ Error in select_fund [{index}]: {e}")



def extract_comparison_table_basics(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "peer-comparison-tab"})
    if not table:
        raise ValueError("❌ 'peer-comparison-tab' table not found.")

    thead = table.find("thead")
    if thead is None:
        raise ValueError("❌ Table header ('thead') not found.")

    header_cells = thead.find_all("th")[1:]  # skip first empty cell
    fund_names = [th.get_text(strip=True) for th in header_cells]

    tbody = table.find("tbody")
    if tbody is None:
        raise ValueError("❌ Table body ('tbody') not found.")

    rows = []
    for tr in tbody.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < len(fund_names) + 1:
            continue
        metric = cells[0].get_text(strip=True)
        values = [td.get_text(strip=True) for td in cells[1:]]
        rows.append([metric] + values)

    df = pd.DataFrame(rows, columns=["Metric"] + fund_names)

    mf_basics = df.copy()

    if 'Metric' in mf_basics.columns:
        mf_basics.set_index('Metric', inplace=True)

    # Drop the unwanted rows
    mf_basics_cleaned = mf_basics.drop(["VR Rating", "Our Opinion"])

    # Transpose the DataFrame: rows ↔ columns
    mf_basics_transposed = mf_basics_cleaned.transpose()

    # Reset index (optional, for cleaner display)
    mf_basics_transposed.reset_index(inplace=True)
    mf_basics_transposed.rename(columns={"index": "Fund Name"}, inplace=True)

    # Show the result
    # print(mf_basics_transposed)

    return mf_basics_transposed


def extract_trailing_returns_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "trailingReturnTabs"})
    if not table:
        raise ValueError("❌ Trailing Returns table not found.")

    # Extract headers
    thead = table.find("thead")
    if not thead:
        raise ValueError("❌ Table header ('thead') not found in trailing returns.")

    header_cells = thead.find_all("th")[1:]  # skip first empty cell
    fund_names = [th.get_text(strip=True) for th in header_cells]

    # Extract body
    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("❌ Table body ('tbody') not found in trailing returns.")

    rows = []
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < len(fund_names) + 1:
            continue
        metric = tds[0].get_text(strip=True)
        values = [td.get_text(strip=True) for td in tds[1:]]
        rows.append([metric] + values)

    # Create DataFrame
    df = pd.DataFrame(rows, columns=["Return Period"] + fund_names)

    # Set "Return Period" as index
    df.set_index("Return Period", inplace=True)

    # Transpose and clean for easier comparison
    trailing_returns = df.transpose().reset_index()
    trailing_returns.rename(columns={"index": "Fund Name"}, inplace=True)

    # print(trailing_returns)
    return trailing_returns


def extract_risk_ratios_table(html: str) -> pd.DataFrame:
    
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "riskRatiosTabs"})
    if not table:
        raise ValueError("❌ Risk Ratios table not found.")


    # Try finding all rows in the table
    rows = table.find_all("tr")
    if not rows:
        raise ValueError("❌ No rows found in table.")

    # Find header row (the one with fund names)
    header_row = rows[0]
    header_cells = header_row.find_all("th")[1:]  # Skip the first blank th
    if not header_cells:
        raise ValueError("❌ No header cells found.")

    fund_names = [cell.get_text(strip=True) for cell in header_cells]

    # Extract the data rows
    data = []
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) < len(fund_names) + 1:
            continue  # Skip incomplete rows

        metric_name = cells[0].get_text(strip=True)
        values = [cell.get_text(strip=True) for cell in cells[1:]]
        data.append([metric_name] + values)

    # Form DataFrame
    df = pd.DataFrame(data, columns=["Metric"] + fund_names)
    df = df.set_index("Metric").transpose().reset_index()
    df = df.rename(columns={"index": "Fund Name"})

    # print(df)
    return df


def extract_asset_allocation_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "asssetAllocationTabs"})
    if not table:
        raise ValueError("❌ Asset Allocation table not found.")

    # Extract column headers (fund names)
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")[1:]]  # skip first blank column

    # Extract rows
    row_labels = []
    data = []
    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        row_labels.append(tds[0].get_text(strip=True))
        values = [td.get_text(strip=True) for td in tds[1:]]
        data.append(values)

    # Create DataFrame
    df = pd.DataFrame(data, index=row_labels, columns=headers)
    df = df.transpose().reset_index()
    df.rename(columns={"index": "Fund Name"}, inplace=True)
    # print(df)
    return df.reset_index()


def extract_sector_distribution_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "sectorDistributionTabs"})
    if not table:
        raise ValueError("❌ Sector Distribution table not found.")

    # Extract headers (fund names)
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")[1:]]  # Skip first "Sectors"

    # Extract rows
    data = []
    row_labels = []

    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        sector_name = tds[0].get_text(strip=True)
        values = [td.get_text(strip=True) for td in tds[1:]]
        row_labels.append(sector_name)
        data.append(values)

    # Create DataFrame
    df = pd.DataFrame(data, index=row_labels, columns=headers)

    df = df.transpose().reset_index()
    df.rename(columns={"index": "Fund Name"}, inplace=True)

    # print(df)
    return df.reset_index()


def extract_fund_holdings_summary_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": "holdingtables"})
    if not table:
        raise ValueError("❌ Fund Holdings Summary table not found.")

    # Extract fund names from the <thead>
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")[1:]]  # Skip first empty column

    # Extract metric rows from the <tbody>
    data = []
    row_labels = []

    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        metric_name = tds[0].get_text(strip=True)
        values = [td.get_text(strip=True) for td in tds[1:]]
        row_labels.append(metric_name)
        data.append(values)

    # Create DataFrame
    df = pd.DataFrame(data, index=row_labels, columns=headers)
    df = df.transpose().reset_index()
    df.rename(columns={"index": "Fund Name"}, inplace=True)

    # print(df)
    return df.reset_index(drop=True)


def compare_and_extract_funds(funds_to_search, flag = True):
    options = uc.ChromeOptions()

    # if headless:
    #     options.add_argument("--headless=new")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    # options.add_argument("window-size=1920,1080")

    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36")
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(version_main=140, options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # 🔐 LOGIN
        try:
            driver.get("https://www.valueresearchonline.com/login")
            time.sleep(5)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Log in with password')]"))).click()
            wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys("taswinikumar69@gmail.com")
            wait.until(EC.element_to_be_clickable((By.ID, "proceed-btn"))).click()
            time.sleep(3)
            wait.until(EC.presence_of_element_located((By.ID, "login_password"))).send_keys("Value*0321")
            wait.until(EC.element_to_be_clickable((By.ID, "login-btn"))).click()
            time.sleep(5)
            wait.until(EC.presence_of_element_located((By.ID, "navbarDropdown-my-investment")))
            print("✅ Logged in successfully")
        except Exception as e:
            print(f"❌ Login failed: {e}")

        # 🔄 FUND COMPARE
        driver.get("https://www.valueresearchonline.com/funds/fund-compare/")
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.ID, "navbarDropdown-my-investment")))


        # -------- clear the five fund-search boxes ----------
        input_ids = ["peer-fund-search"] + [f"peer-fund-search{i}" for i in range(2, 6)]

        for idx, field_id in enumerate(input_ids, start=1):
            try:
                # wait until the input is visible & interactable
                input_box = wait.until(EC.visibility_of_element_located((By.ID, field_id)))

                # make sure it isn’t hidden behind the sticky ad/header
                # Scroll the input box into view, forcing it to be visible even if inside a scrollable div
                driver.execute_script("""
                    const element = arguments[0];
                    element.scrollIntoView({block: 'center', inline: 'nearest'});
                    const rect = element.getBoundingClientRect();
                    if (rect.top < 0 || rect.bottom > window.innerHeight) {
                        window.scrollBy(0, rect.top - 150);
                    }
                """, input_box)

                time.sleep(0.3)

                # clear only if something is already typed
                if (input_box.get_attribute("value") or "").strip():
                    input_box.click()
                    input_box.send_keys(Keys.CONTROL, "a")
                    input_box.send_keys(Keys.BACKSPACE)
                    print(f"✅ Cleared input box {idx}")
                else:
                    print(f"ℹ️ Input box {idx} already empty")

            except TimeoutException:
                print(f"⚠️ Timeout locating {field_id}")
            except Exception as e:
                print(f"⚠️ Error interacting with {field_id}: {e}")






        for idx, fund in enumerate(funds_to_search[:5]):
            select_fund(driver, wait, fund, index=idx)
            time.sleep(1)

        try:
            compare_btn = wait.until(EC.presence_of_element_located((By.ID, "compare_fund")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", compare_btn)
            time.sleep(5)
            compare_btn.click()
            print("✅ Clicked 'Compare These Funds'")
        except Exception as e:
            driver.execute_script("arguments[0].click();", compare_btn)

        time.sleep(4)
        os.makedirs("data", exist_ok=True)

        # 📊 BASIC & RETURN TABLES
        html = driver.page_source
        mf_basics = extract_comparison_table_basics(html)
        # if flag:
        #     mf_basics.to_csv("data/mf_basics.csv", index=False)
        #     print("✅ Basic table saved")

        mf_return = extract_trailing_returns_table(html)
        # if flag:
        #     mf_return.to_csv("data/mf_return.csv", index=False)
        #     print("✅ Return table saved")

        # 📉 RISK RATIOS
        driver.execute_script("document.querySelector(\"a[href='#riskRatiosTab']\").click()")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[@id='riskRatiosTabs']//tr[td]")))
        mf_risk = extract_risk_ratios_table(driver.page_source)
        # if flag:
        #     mf_risk.to_csv("data/mf_risk.csv", index=False)
        #     print("✅ Risk Ratio table saved")

        # 📊 ASSET ALLOCATION
        driver.execute_script("document.querySelector(\"a[href='#asssetAllocationTab']\").click()")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[@id='asssetAllocationTabs']//tr[td]")))
        mf_asset = extract_asset_allocation_table(driver.page_source)
        # if flag:
        #     mf_asset.to_csv("data/mf_asset_allocation.csv", index=False)
        #     print("✅ Asset Allocation table saved")

        # 📊 SECTOR DISTRIBUTION
        driver.execute_script("document.querySelector(\"a[href='#sectorDistributionTab']\").click()")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[@id='sectorDistributionTabs']//tr[td]")))
        df_sector = extract_sector_distribution_table(driver.page_source)
        # if flag:
        #     df_sector.to_csv("data/mf_sector_distribution.csv", index=False)
        #     print("✅ Sector Distribution table saved")

        # 📋 HOLDINGS
        driver.execute_script("document.querySelector(\"a[href='#holdingsTab']\").click()")
        wait.until(EC.presence_of_element_located((By.XPATH, "//table[@id='holdingtables']//tr[td]")))
        df_holdings = extract_fund_holdings_summary_table(driver.page_source)
        # if flag:
        #     df_holdings.to_csv("data/mf_holdings.csv", index=False)
        #     print("✅ Holdings table saved")

        # ✅ Merge all tables on 'Fund Name'
        for df in [mf_basics, mf_return, mf_risk, mf_asset, df_sector, df_holdings]:
            df.columns = df.columns.str.strip()  # Clean column names

        merged_df = mf_basics \
            .merge(mf_return, on="Fund Name", how="outer") \
            .merge(mf_risk, on="Fund Name", how="outer") \
            .merge(mf_asset, on="Fund Name", how="outer") \
            .merge(df_sector, on="Fund Name", how="outer") \
            .merge(df_holdings, on="Fund Name", how="outer")

        merged_df.to_csv("data/mf_merged.csv", index=False)
        print("✅ Tables merged and saved successfully")

        return merged_df 

    except Exception as e:
        print("❌ Error:", e)
    finally:
        driver.quit()
        pass



# def fetch_and_prepare_fund_table(fund_list):

#     # Step 1: Remove duplicates
#     unique_funds = list(set(fund_list))

#     # Step 2: If 6 or fewer, fetch once
#     if len(unique_funds) < 6:
#         extracted_funds_df = compare_and_extract_funds(unique_funds, flag=True)
#         df = extracted_funds_df.set_index("Fund Name").T.reset_index()
#         df.rename(columns={"index": "Metric"}, inplace=True)
#         return df

#     # Step 3: Split and fetch in two batches
#     mid = len(unique_funds) // 2
#     batch1 = unique_funds[:mid]
#     batch2 = unique_funds[mid:]

#     df1 = compare_and_extract_funds(batch1, flag=True).set_index("Fund Name").T.reset_index()
#     df2 = compare_and_extract_funds(batch2, flag=True).set_index("Fund Name").T.reset_index()

#     df1.rename(columns={"index": "Metric"}, inplace=True)
#     df2.rename(columns={"index": "Metric"}, inplace=True)

#     # Step 4: Merge both dataframes on Metric
#     merged_df = df1.merge(df2, on="Metric", how="outer")

#     return merged_df


def fetch_and_prepare_fund_table(fund_list):
    # Step 1: Remove duplicates
    unique_funds = list(dict.fromkeys(fund_list))  # preserves original order

    # Step 2: If 6 or fewer, fetch once
    if len(unique_funds) <= 5:
        extracted_funds_df = compare_and_extract_funds(unique_funds, flag=True)
        df = extracted_funds_df.set_index("Fund Name").T.reset_index()
        df.rename(columns={"index": "Metric"}, inplace=True)
        return df

    # Step 3: Split and fetch in two batches
    mid = len(unique_funds) // 2
    batch1 = unique_funds[:mid]
    batch2 = unique_funds[mid:]

    df1 = compare_and_extract_funds(batch1, flag=True).set_index("Fund Name").T.reset_index()
    df2 = compare_and_extract_funds(batch2, flag=True).set_index("Fund Name").T.reset_index()

    df1.rename(columns={"index": "Metric"}, inplace=True)
    df2.rename(columns={"index": "Metric"}, inplace=True)

    # Step 4: Merge both dataframes on Metric
    merged_df = df1.merge(df2, on="Metric", how="outer")

    # Step 5: Reorder based on df1's Metric order
    metric_order = df1["Metric"].tolist()
    merged_df["Metric"] = pd.Categorical(merged_df["Metric"], categories=metric_order, ordered=True)
    merged_df = merged_df.sort_values("Metric").reset_index(drop=True)

    return merged_df



def format_fund_analysis(fund_data: dict) -> str:
    html = "<div class='llm-analysis'>"
    html += "<h3>📊 LLM Investment Analysis</h3>"
    html += "<h4>1. Analysis with Strengths and Weaknesses of Each Fund:</h4>"

    for fund_name, details in fund_data.items():
        html += f"<h4>{fund_name}</h4>"

        # Strengths
        strengths = details.get("Strengths", [])
        if strengths:
            html += "<strong>Strengths:</strong><ul>"
            for s in strengths:
                html += f"<li>{s.strip()}</li>"
            html += "</ul>"

        # Weaknesses
        weaknesses = details.get("Weaknesses", [])
        if weaknesses:
            html += "<strong>Weaknesses:</strong><ul>"
            for w in weaknesses:
                html += f"<li>{w.strip()}</li>"
            html += "</ul>"

    html += "</div>"
    return html
