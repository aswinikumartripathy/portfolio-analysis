from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse,StreamingResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
import pandas as pd
from typing import Optional, List
import traceback
import tempfile
from io import BytesIO, StringIO
import matplotlib.pyplot as plt


# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_experimental.utilities import PythonREPL
from fastapi.responses import RedirectResponse
from langchain_ollama import ChatOllama
from fastapi.staticfiles import StaticFiles


from typing import List


from extract_fund import compare_and_extract_funds, fetch_and_prepare_fund_table, format_fund_analysis
from portfolio import prepare_and_generate_html_list, create_monthly_chart
from llm_analyser import analyze_mutual_funds_with_llama, analyze_mutual_funds_with_gpt, analyze_mutual_funds_portfolio_with_gpt
from cas_parser import (
    remove_pdf_password,
    extract_text_from_pdf,
    ask_gpt_for_portfolio_table,
    ask_llama_for_portfolio_table,
    extract_investment_table,
    markdown_table_to_dataframe,
    get_market_cap,
    get_clean_scheme_market_value,
    extract_portfolio_table_from_cas,
    merge_portfolios
)
from transaction import calculate_capital_flow_kpis

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ Global in-memory portfolio store
portfolio_df: Optional[pd.DataFrame] = None
category_global: Optional[str] = None


@app.get("/dashboard", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/upload-portfolio-form", response_class=HTMLResponse)
async def show_upload_form(request: Request):
    return templates.TemplateResponse("upload_portfolio_form.html", {"request": request})

@app.get("/transactions", response_class=HTMLResponse)
async def show_upload_form(request: Request):
    return templates.TemplateResponse("upload_transaction_form.html", {"request": request})



@app.post("/portfolio-cas-pdf", response_class=HTMLResponse)
async def upload_cas(
    request: Request,
    file: UploadFile = File(...),
    is_pwd_protected: bool = Form(False),
    password: Optional[str] = Form(None),
):
    print("inside cas upload")
    global portfolio_df

    upload_path = f"temp_{file.filename}"
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Decide which path to feed to text extraction
    pdf_input_path = upload_path

    try:
        # If toggle is ON, we must have a password and we unlock first
        if is_pwd_protected:
            if not password:
                return templates.TemplateResponse(
                    "upload.html",
                    {"request": request, "error": "Password is required for a protected CAS."}
                )
            pdf_input_path = remove_pdf_password(upload_path, password)

        # # for using gpt to extract portfolio
        # pdf_text = extract_text_from_pdf(pdf_input_path)
        # df = ask_gpt_for_portfolio_table(pdf_text)
        # df = markdown_table_to_dataframe(df)

        # using python to extract portfolio
        df = extract_portfolio_table_from_cas(pdf_input_path)
        df["Scheme Name"] = df["Scheme Name"].str.replace(r"^[\w\s]+ -\s*", "", regex=True)
        df["Scheme Name"] = df["Scheme Name"].str.replace(r"\s*\(.*?\)", "", regex=True)
        
        df["Market Cap"] = df["Scheme Name"].apply(get_market_cap)

        df.to_csv("data/portfolio_summary.csv", index=False)

        portfolio_df = df  # ✅ Save to global memory

        return templates.TemplateResponse(
            "portfolio.html",
            {"request": request, "portfolio": df}
        )

    except Exception as e:
        return templates.TemplateResponse(
            "upload.html",
            {"request": request, "error": str(e)}
        )

    finally:
        # Clean up temp files
        try:
            if os.path.exists(upload_path):
                os.remove(upload_path)
        except:
            pass
        try:
            if is_pwd_protected and pdf_input_path != upload_path and os.path.exists(pdf_input_path):
                os.remove(pdf_input_path)
        except:
            pass

@app.post("/portfolio-csv", response_class=HTMLResponse)
async def upload_csv(
    request: Request,
    csvfiles: List[UploadFile] = File(...),
    cleaning_required: str = Form(...)
):
    global portfolio_df
    try:
        merged_df_list = []

        for csvfile in csvfiles:
            csv_path = f"temp_{csvfile.filename}"
            with open(csv_path, "wb") as f:
                shutil.copyfileobj(csvfile.file, f)

            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.strip()

            if cleaning_required.lower() == "yes":
                df["Scheme Name"] = df["Scheme Name"].str.replace(r"^[\w\s]+ -\s*", "", regex=True)
                df["Scheme Name"] = df["Scheme Name"].str.replace(r"\s*\(.*?\)", "", regex=True)

            required_cols = ["Folio No", "Scheme Name", "Unit Balance", "NAV", "Market Value", "ISIN"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"❌ CSV {csvfile.filename} missing required columns.")

            if "Market Cap" not in df.columns:
                df["Market Cap"] = df["Scheme Name"].apply(get_market_cap)

            merged_df_list.append(df)
            os.remove(csv_path)

        # ✅ Merge all uploaded DataFrames into one
        combined_df = pd.concat(merged_df_list, ignore_index=True)

        # ✅ Use your merge function to aggregate by ISIN
        final_df = merge_portfolios(combined_df, pd.DataFrame())

        final_df.to_csv("data/portfolio_summary.csv", index=False)
        portfolio_df = final_df

        return templates.TemplateResponse("portfolio.html", {
            "request": request,
            "portfolio": final_df
        })

    except Exception as e:
        return templates.TemplateResponse("upload_error.html", {
            "request": request,
            "error": str(e)
        })


@app.post("/portfolio-multi", response_class=HTMLResponse)
async def merge_csvs(
    request: Request,
    csvfile1: UploadFile = File(...),
    csvfile2: UploadFile = File(...)
):
    global portfolio_df
    try:
        # Read both files into DataFrames
        df1 = pd.read_csv(csvfile1.file)
        df2 = pd.read_csv(csvfile2.file)

        # ✅ Call your existing merge function
        merged_df = merge_portfolios(df1, df2)

        # Save & keep in memory
        merged_df.to_csv("data/portfolio_summary.csv", index=False)
        portfolio_df = merged_df

        return templates.TemplateResponse("portfolio.html", {
            "request": request,
            "portfolio": merged_df
        })

    except Exception as e:
        return templates.TemplateResponse("upload_error.html", {
            "request": request,
            "error": str(e)
        })



@app.get("/download-csv")
async def download_csv():
    csv_path = "data/portfolio_summary.csv"
    if os.path.exists(csv_path):
        return FileResponse(csv_path, media_type='text/csv', filename="portfolio_summary.csv")
    return {"error": "CSV file not found."}

@app.get("/investment-plan", response_class=HTMLResponse)
async def show_investment_form(request: Request):
    return templates.TemplateResponse("investment_plan.html", {"request": request})

@app.post("/investment-plan", response_class=HTMLResponse)
async def handle_investment_plan(
    request: Request,
    amount: int = Form(...),
    category: str = Form(...),
    funds: List[str] = Form(...),
    action: str = Form(...)
):  
    
    category_global = category  # Save category globally for use in chat
    # print(f"Received funds: {funds}")

    print(f"Extracting your portfolio and funds you are targeting funds for {category}...")
    portfolio_local_df = pd.read_csv("data/portfolio_summary.csv")
    category = category_global.lower()
    # print(category)
    market_cap_portfolio_df = portfolio_local_df[portfolio_local_df["Market Cap"].str.lower() == category.lower()]
    # print(market_cap_portfolio_df)
    json_path = "src/scheme_name.json"
    invested_df = get_clean_scheme_market_value(market_cap_portfolio_df, json_path) #contains value research fund name and market value
    future_investment = invested_df["Market Value"].sum() + amount
    # print(cleaned_df)
    scheme_list = invested_df["Scheme Name"].tolist()


    combined_list = list(set(scheme_list + funds))
    combined_list = sorted(combined_list)
    print("Combined list = ", combined_list)
    print("Fund list = ", funds)
    print("Scheme list = ", scheme_list)
    # extracted_funds_df = compare_and_extract_funds(combined_list, flag=True)
    # df = extracted_funds_df.set_index("Fund Name").T.reset_index()

    extracted_df = fetch_and_prepare_fund_table(combined_list)
    extracted_df.rename(columns={"index": "Metric"}, inplace=True)
    print("✅ Extracted investment funds successfully.")

    # print(extracted_df)
    # Get response from LLM
    if action == "deep":
        analysis_text = analyze_mutual_funds_portfolio_with_gpt(extracted_df, amount, future_investment, invested_df, category, model="gpt-4-turbo")
    else:
        analysis_text = analyze_mutual_funds_portfolio_with_gpt(extracted_df, amount, future_investment, invested_df, category, model="gpt-3.5-turbo")
    # html_rslt = format_fund_analysis(analysis_text)
    
    return templates.TemplateResponse("investment_plan.html", {
        "request": request,
        "message": f"✅ Plan created for ₹{amount} in {category} category with selected funds: {', '.join(funds)}",
        # "columns": columns,
        "table_data": extracted_df,
        "analysis": analysis_text,
        "funds_looking_for": combined_list,
        "funds_invested": scheme_list
    })


@app.post("/recent-investments")
async def recent_investments(
    file: list[UploadFile] = File(...),  # now accepts multiple files
    analysis_type: str = Form(...),
    from_date: str = Form(None),
    to_date: str = Form(None)
):
    try:
        dfs = []
        # Read each uploaded file into a DataFrame
        for f in file:
            contents = await f.read()
            ext = f.filename.split('.')[-1].lower()

            if ext in ['xlsx', 'xls']:
                df_part = pd.read_excel(BytesIO(contents))
            elif ext == 'csv':
                df_part = pd.read_csv(BytesIO(contents))
            else:
                return {"error": f"Unsupported file format: {f.filename}"}

            dfs.append(df_part)

        if not dfs:
            return {"error": "No valid files uploaded"}

        # Merge all DataFrames
        df = pd.concat(dfs, ignore_index=True)

        # Parse date column
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

        # Apply date filters if provided
        if from_date:
            df = df[df['date'] >= pd.to_datetime(from_date)]
        if to_date:
            df = df[df['date'] <= pd.to_datetime(to_date)]

        kpis = calculate_capital_flow_kpis(df)

        # Normalize trade type
        df['type'] = df['type'].astype(str).str.strip().str.upper()

        # Assign negative value for SELL trades
        df['trade_val_signed'] = df.apply(
            lambda row: -row['trade_val'] if row['type'] == 'SELL' else row['trade_val'],
            axis=1
        )

        # Decide grouping
        if from_date and to_date:
            start = pd.to_datetime(from_date)
            end = pd.to_datetime(to_date)

            # Group into 30-day bins starting from 'from_date'
            summary = (
                df.groupby(pd.Grouper(key='date', freq='30D', origin=start))
                  ['trade_val_signed']
                  .sum()
                  .reset_index()
                  .rename(columns={'trade_val_signed': 'net_investment'})
            )

            # Keep only bins within the range
            summary = summary[(summary['date'] >= start) & (summary['date'] <= end)]

            # Calculate end date for each bin (cap at to_date)
            summary['end_date'] = summary['date'] + pd.Timedelta(days=29)
            summary.loc[summary['end_date'] > end, 'end_date'] = end

            # Label bins as "start → end"
            summary['label'] = (
                summary['date'].dt.strftime('%d-%b-%Y') + " → " +
                summary['end_date'].dt.strftime('%d-%b-%Y')
            )

            x_col = 'label'
            title = f"Recent Investments (30-Day Periods)\n{from_date} to {to_date}"

        else:
            # Monthly grouping
            df['period_start'] = df['date'].dt.to_period('M').dt.start_time
            df['period_end'] = df['period_start'] + pd.offsets.MonthEnd(0)

            summary = (
                df.groupby(['period_start', 'period_end'])['trade_val_signed']
                  .sum()
                  .reset_index()
                  .rename(columns={'trade_val_signed': 'net_investment'})
            )

            # Label as "start → end"
            summary['label'] = (
                summary['period_start'].dt.strftime('%d-%b-%Y') + " → " +
                summary['period_end'].dt.strftime('%d-%b-%Y')
            )

            x_col = 'label'
            title = "Monthly Net Investments"

        # Plot bar chart
        fig, ax = plt.subplots(figsize=(14, 8))
        colors = ['#007bff' if val >= 0 else '#ff4d4d'
                  for val in summary['net_investment']]
        bars = ax.bar(summary[x_col], summary['net_investment'], color=colors)

        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5 if height >= 0 else -15),
                        textcoords="offset points",
                        ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=9, fontweight='bold')

        ax.set_title(title, fontsize=16)
        ax.set_xlabel('Period')
        ax.set_ylabel('Net Investment Amount (₹)')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45, ha='right')

        # Save to buffer
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        return {"error": str(e)}



@app.api_route("/portfolio-analysis", methods=["GET", "POST"], response_class=HTMLResponse)
async def show_portfolio_distribution(
    request: Request,
    file: UploadFile = File(None),
    analysis_type: str = Form(None)  # tells if "Advanced Analysis" was clicked
):
    global portfolio_df, transaction_df

    transaction_df = None
    monthwise_df = None
    stacked_chart_base64 = None

    # Process uploaded Excel/CSV file, if any
    if file and file.filename:
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1].lower()

        try:
            if ext == ".xls":
                transaction_df = pd.read_excel(BytesIO(contents), engine="xlrd")
            elif ext == ".xlsx":
                transaction_df = pd.read_excel(BytesIO(contents), engine="openpyxl")
            elif ext == ".csv":
                transaction_df = pd.read_csv(StringIO(contents.decode("utf-8")))
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {e}")

        # ✅ Validate required columns
        required_cols = {"date", "type", "trade_val"}
        missing_cols = required_cols - set(transaction_df.columns)
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Missing columns: {missing_cols}")

        # ✅ Clean & type-cast
        transaction_df["TRADE_DATE"] = pd.to_datetime(
            transaction_df["date"] + " " + transaction_df.get("time", ""),
            errors="coerce",
            dayfirst=True,
        )
        transaction_df["AMOUNT"] = pd.to_numeric(transaction_df["trade_val"], errors="coerce")

        # ✅ Convert BUY to + and SELL to -
        transaction_df.loc[
            transaction_df["type"].str.upper() == "SELL", "AMOUNT"
        ] *= -1

        transaction_df.dropna(subset=["TRADE_DATE", "AMOUNT"], inplace=True)

    # Advanced analysis: build month-wise net investment summary
    # Month-wise net investment summary
    if analysis_type == "advanced" and transaction_df is not None and not transaction_df.empty:
        # Create YearMonth column
        transaction_df["YearMonth"] = transaction_df["TRADE_DATE"].dt.to_period("M")

        # Group by month -> net investment (BUY positive, SELL negative)
        monthwise_df = (
            transaction_df.groupby("YearMonth")["AMOUNT"]
            .sum()
            .reset_index()
            .rename(columns={"YearMonth": "Month", "AMOUNT": "Total_Investment"})
        )

        # ✅ Now monthwise_df has columns: Month | Total_Investment
        stacked_chart_base64 = create_monthly_chart(monthwise_df)




    # Ensure base portfolio exists
    if portfolio_df is None:
        return RedirectResponse("/", status_code=303)

    # Prepare summary context
    context = prepare_and_generate_html_list(portfolio_df)

    expected_distribution = {
        "Large Cap": 30,
        "Mid Cap": 25,
        "Small Cap": 25,
        "Infrastructure": 15,
        "Gold": 5,
    }

    return templates.TemplateResponse(
        "investment_analysis.html",
        {
            "request": request,
            "df": context["df"],
            "overall_totals": context["overall_totals"],
            "amc_totals": context["amc_totals"],
            "total_cost": context["total_cost"],
            "total_market": context["total_market"],
            "total_return_pct": context["total_return_pct"],
            "total_funds": context["total_funds"],
            "total_pnl": context["total_pnl"],
            "pnl_class": context["pnl_class"],
            "chart_base64": context["chart_base64"],
            "expected_distribution": expected_distribution,
            "cap_wise_funds": context["cap_wise_funds"],
            "monthwise_df": monthwise_df.to_html(classes="table table-striped", index=False)
                              if monthwise_df is not None else None,
            "stacked_chart_base64": stacked_chart_base64
        }
    )



@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(BytesIO(contents))

    # Ensure numeric
    df["TRADE_DATE"] = pd.to_datetime(df["TRADE_DATE"], errors="coerce")
    df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce")
    df = df.dropna(subset=["TRADE_DATE", "AMOUNT"])

    month_summary = (
        df.groupby(df["TRADE_DATE"].dt.to_period("M"))["AMOUNT"]
        .sum()
        .reset_index()
    )
    month_summary["TRADE_DATE"] = month_summary["TRADE_DATE"].astype(str)
    month_summary.rename(columns={"TRADE_DATE": "Month", "AMOUNT": "Investment"}, inplace=True)

    return JSONResponse(content=month_summary.to_dict(orient="records"))




@app.post("/chat")
async def chat(query: str = Form(...)):
    global portfolio_df

    if portfolio_df is None:
        return {"response": "Please upload your portfolio first."}

    try:
        # Use create_pandas_dataframe_agent with dangerous code enabled
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            openai_api_key=os.getenv("OPENAI_API_KEY")  # or set directly as string if needed
        )

        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=portfolio_df,
            verbose=True,
            agent_type="openai-tools",
            handle_parsing_errors=True,
            **{"allow_dangerous_code": True}
        )

        response = agent.run(query)
        return {"response": response}

    except Exception as e:
        return JSONResponse(content={"response": f"❌ Error: {str(e)}"}, status_code=500)
    

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """
    Endpoint used by the chatbot UI (📎). Accepts a PDF (or other),
    extracts text via your cas_parser helpers, converts to DataFrame,
    and stores it in memory as portfolio_df.
    """
    global portfolio_df
    tmpfile = None
    try:
        # Save uploaded file to a temp file
        suffix = os.path.splitext(file.filename)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
            tmpfile = tf.name
            shutil.copyfileobj(file.file, tf)

        # Try to extract text. If your PDFs are password-protected you'll need to call remove_pdf_password first.
        pdf_text = extract_text_from_pdf(tmpfile)

        # Use your helper to ask GPT -> markdown table -> DataFrame
        markdown_table = ask_gpt_for_portfolio_table(pdf_text)
        df = markdown_table_to_dataframe(markdown_table)

        # Derive Market Cap column if possible
        if "Scheme Name" in df.columns:
            df["Market Cap"] = df["Scheme Name"].apply(get_market_cap)

        # persist to data folder and set global
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/portfolio_summary.csv", index=False)
        portfolio_df = df

        return JSONResponse({"response": "✅ PDF processed and data loaded into the chatbot. Ask me anything about it now."})
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse({"response": f"❌ Error processing PDF: {str(e)}", "trace": tb}, status_code=500)
    finally:
        try:
            if tmpfile and os.path.exists(tmpfile):
                os.remove(tmpfile)
        except Exception:
            pass


@app.post("/api/chat")
async def api_chat(payload: dict):
    global portfolio_df
    try:
        message = payload.get("message") if isinstance(payload, dict) else None
        use_gpt = payload.get("use_gpt", False)  # Expecting this boolean

        if not message:
            return JSONResponse({"response": "❌ No message provided."}, status_code=400)

        if portfolio_df is None:
            return JSONResponse({"response": "❌ No portfolio data loaded. Upload a PDF or CSV first."}, status_code=400)

        df_preview = portfolio_df.to_csv(index=False)

        if use_gpt:
            # Compose prompt including portfolio data for GPT
            prompt = f"""
            You are a portfolio analysis assistant.
            Here is the portfolio data:
            {df_preview}

            Question: {message}
            Answer clearly and concisely.
            """

            # Call GPT model (example with OpenAI API client)
            # Replace with your GPT client call
            from openai import OpenAI
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            result = completion.choices[0].message.content

        else:
            # Ollama path (your existing code)
            llm = ChatOllama(model="llama3", temperature=0)
            prompt = f"""
            You are a portfolio analysis assistant.
            Here is the portfolio data:
            {df_preview}

            Question: {message}
            Answer as clearly and concisely as possible.
            """
            result = llm.invoke(prompt).content

        return {"response": result}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return JSONResponse({"response": f"❌ Error: {str(e)}", "trace": tb}, status_code=500)