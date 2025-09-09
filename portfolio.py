# import pandas as pd
# import plotly.graph_objects as go
# import base64
# from io import BytesIO
# import re

# def prepare_and_generate_html_list(df):
#     # Rename column for clarity
#     df = df.rename(columns={'Market Cap': 'Sector'})

#     # Extract AMC name from Scheme Name
#     df['AMC'] = df['Scheme Name'].str.extract(
#         r'(SBI|Nippon|HDFC|ICICI|Motilal|Bandhan|DSP|Franklin|Aditya|Tata|Edelweiss|Invesco|Canara|Mirae|LIC|PGIM|Mahindra|Baroda|Quant)',
#         flags=re.IGNORECASE,
#         expand=False
#     ).str.upper().fillna('OTHER')


#     df['AMC'] = df['AMC'].str.strip()
#     print(df.head())

#     # Calculate Return %
#     df['Return %'] = ((df['Market Value'] - df['Cost Value']) / df['Cost Value']) * 100
#     df['Market Value'] = df['Market Value'].round(2)
#     df['Cost Value'] = df['Cost Value'].round(2)
#     df['Return %'] = df['Return %'].round(2)

#     # Compute sector totals and distribution %
#     sector_totals = df.groupby('Sector')['Market Value'].sum().reset_index()
#     sector_totals.rename(columns={'Market Value': 'Sector Total'}, inplace=True)
#     df = df.merge(sector_totals, on='Sector')
#     df['Distribution %'] = (df['Market Value'] / df['Sector Total']) * 100
#     df['Distribution %'] = df['Distribution %'].round(2)

#     # Define desired order
#     sector_order = ["Large Cap", "Mid Cap", "Small Cap", "Infrastructure", "Gold", "Tax Saving"]

#     # Convert Sector column to ordered categorical
#     df['Sector'] = pd.Categorical(df['Sector'], categories=sector_order, ordered=True)

#     # Sort overall_totals and df using that order
#     overall_totals = df.groupby('Sector')['Market Value'].sum().reset_index()
#     overall_totals = overall_totals.sort_values('Sector')

#     # Also reorder sector-wise breakdown
#     df = df.sort_values(['Sector', 'Distribution %'], ascending=[True, False])



    

#     # AMC-wise totals
#     amc_totals = df.groupby('AMC')[['Cost Value', 'Market Value']].sum().reset_index()
#     amc_totals['Return %'] = ((amc_totals['Market Value'] - amc_totals['Cost Value']) / amc_totals['Cost Value']) * 100
#     amc_totals['Distribution %'] = (amc_totals['Market Value'] / amc_totals['Market Value'].sum()) * 100
#     amc_totals = amc_totals.round(2)
#     amc_totals = amc_totals.sort_values(by='Market Value', ascending=False)

#     # Donut chart
#     fig = go.Figure(data=[go.Pie(labels=overall_totals['Sector'],
#                                  values=overall_totals['Market Value'],
#                                  hole=.5, textinfo='label+percent')])
#     fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

#     # Summary values
#     total_cost = df['Cost Value'].sum().round(2)
#     total_market = df['Market Value'].sum().round(2)
#     total_return_pct = (((total_market - total_cost) / total_cost) * 100).round(2)
#     total_funds = df['Scheme Name'].nunique()
#     total_pnl = total_market - total_cost
#     pnl_class = "positive" if total_pnl >= 0 else "negative"

#     # Encode chart
#     buffer = BytesIO()
#     fig.write_image(buffer, format='png')
#     buffer.seek(0)
#     chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
#     buffer.close()

#     # HTML output start
#     html_output = f"""
#     <html>
#     <head>
#         <title>Sector-wise Mutual Fund Allocation</title>
#         <style>
#             body {{
#                 font-family: 'Segoe UI', sans-serif;
#                 background-color: #f4f6f9;
#                 margin: 0;
#                 padding: 30px 40px;
#                 color: #2c3e50;
#             }}
#             h1 {{
#                 text-align: center;
#                 font-size: 32px;
#                 color: #2c3e50;
#                 margin-bottom: 20px;
#             }}
#             .top-section {{
#                 display: flex;
#                 justify-content: space-between;
#                 gap: 20px;
#                 margin-bottom: 40px;
#                 align-items: stretch;
#             }}
#             .left-table {{
#                 width: 50%;
#                 padding-right: 20px;
#                 box-sizing: border-box;
#             }}
#             .summary-table {{
#                 flex: 1;
#                 width: 50%;                          
#                 display: flex;                        
#                 flex-direction: column;
#                 justify-content: stretch;
#                 background: #fff;
#                 padding: 0;                            
#                 border-radius: 10px;
#                 box-shadow: 0 3px 12px rgba(0,0,0,0.06);
#                 overflow: hidden;
#                 box-sizing: border-box;
#                 height: 100%;  
#                 align-self: stretch;

#             }}

#             .summary-table table {{
#                 flex: 1;
#                 width: 100%;
#                 height: 100%;                         
#                 border-collapse: collapse;
#                 font-size: 16px;
#                 table-layout: fixed;
#             }}
#             .summary-table th, .summary-table td {{
#                 padding: 12px 16px;
#                 text-align: left;
#                 border-bottom: 1px solid #f0f0f0;
#             }}
#             .summary-table th {{
#                 background-color: #dceefc;
#                 font-weight: 600;
#                 color: #1f4e79;
#             }}
#             .summary-table td {{
#                 background-color: #fff;
#             }}

#             .donut-chart {{
#                 display: flex;
#                 align-items: center;       /* vertically center content */
#                 justify-content: center;
#                 max-height: 400px;         /* smaller max height */
#                 padding: 20px;             /* add some padding if you want */
#             }}
#             .donut-chart img {{
#                 max-height: 100%;
#                 max-width: 100%;
#                 object-fit: contain;       /* keep full image visible */
#                 display: block;
#                 margin: 0 auto;
#                 border-radius: 10px;
#             }}
#             h2 {{
#                 font-size: 24px;
#                 color: #1f78b4;
#                 margin: 30px 0 10px;
#                 border-left: 5px solid #1f78b4;
#                 padding-left: 10px;
#             }}
#             table {{
#                 width: 100%;
#                 border-collapse: collapse;
#                 margin-bottom: 30px;
#                 table-layout: fixed;
#                 box-shadow: 0 2px 8px rgba(0,0,0,0.08);
#                 border-radius: 8px;
#                 overflow: hidden;
#                 background-color: #fff;
#             }}
#             th, td {{
#                 padding: 12px 15px;
#                 text-align: left;
#                 word-wrap: break-word;
#             }}
#             th {{
#                 background-color: #dceefc;
#                 color: #1f4e79;
#                 font-weight: 600;
#             }}
#             tr:nth-child(even) td {{
#                 background-color: #f4f9fd;
#             }}
#             .kpi-wrapper {{
#                 display: flex;
#                 justify-content: space-between;
#                 align-items: stretch;
#                 padding: 20px;
#                 border-radius: 14px;
#                 background: #fff;
#                 box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#                 margin-bottom: 30px;
#             }}

#             .kpi-section {{
#                 padding: 10px 15px;
#                 text-align: center;
#             }}

#             .kpi-section.wide {{ flex: 0 0 40%; }}
#             .kpi-section.medium {{
#                 flex: 0 0 30%;
#                 display: flex;
#                 flex-direction: column;
#                 justify-content: center;
#                 align-items: center; /* This centers horizontally */
#                 text-align: center;  /* Ensures text is centered */
#             }}

#             /* Divider lines */
#             .kpi-section:not(:last-child) {{
#                 border-right: 1px solid #e0e0e0;
#             }}

#             .kpi-title {{
#                 font-size: 16px;
#                 color: #555;
#                 margin-bottom: 8px;
#             }}

#             .kpi-value {{
#                 font-size: 24px;
#                 font-weight: bold;
#                 color: #2c3e50;
#             }}

#             .kpi-value.big {{
#                 font-size: 32px;
#                 font-weight: bold;
#                 color: #1f4e79;
#             }}

#             .kpi-sub {{
#                 font-size: 14px;
#                 color: #666;
#                 margin-top: 6px;
#             }}

#             # .kpi-section.positive {{
#             #     color: #27ae60 !important;
#             #     background: #fff !important;
#             # }}
#             # .kpi-section.negative {{
#             #     color: #c0392b !important;
#             #     background: #fff !important;
#             # }}

#             .kpi-value.positive {{
#                 color: #27ae60; /* green */
#             }}

#             .kpi-value.negative {{
#                 color: #c0392b; /* red */
#             }}

#             .positive {{
#                 color: #27ae60; /* green */
#                 font-weight: bold;
#             }}

#             .negative {{
#                 color: #c0392b; /* red */
#                 font-weight: bold;
#             }}

#             .summary-table, .donut-chart {{
#                 width: 50%;
#                 height: auto;      /* Let height adjust naturally */
#                 display: flex;
#                 flex-direction: column;
#                 justify-content: stretch;
#                 background: #fff;
#                 padding: 0;
#                 border-radius: 10px;
#                 box-shadow: 0 3px 12px rgba(0,0,0,0.06);
#                 overflow: hidden;
#             }}

#             img {{
#                 display: block;
#             }}
#             h3 {{
#                 font-size: 20px;
#                 color: #4c4949;
#                 margin: 20px 0 10px;
#                 border-left: 4px solid #4c4949;
#                 padding-left: 10px;
#             }}

#         </style>
#     </head>
#     <body>
#         <h1>Investment Portfolio</h1>

        
#         <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
#             <button onclick="downloadPDF()" 
#                     style="background-color: #1f78b4; color: white; padding: 10px 20px; border: none; 
#                         border-radius: 6px; cursor: pointer; font-size: 14px;">
#                 Download PDF
#             </button>
#         </div>

#         <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
#         <script>
#             function downloadPDF() {{
#                 const element = document.body;
#                 const opt = {{
#                     margin:       0.3,
#                     filename: 'investment_portfolio_' + new Date().toISOString().split('T')[0] + '.pdf',
#                     image:        {{ type: 'jpeg', quality: 0.98 }},
#                     html2canvas:  {{ scale: 2 }},
#                     jsPDF:        {{ unit: 'in', format: 'letter', orientation: 'portrait' }}
#                 }};
#                 html2pdf().set(opt).from(element).save();
#             }}
#         </script>
     

#         <div class="kpi-card kpi-wrapper">
#             <div class="kpi-section wide">
#                 <div class="kpi-title">Current Portfolio Value</div>
#                 <div class="kpi-value big">₹{total_market:,.0f}</div>
#                 <div class="kpi-sub">Invested Amount: ₹{total_cost:,.0f}</div>
#             </div>

#             <div class="kpi-section medium">
#                 <div class="kpi-title">Total P&amp;L</div>
#                 <div class="kpi-value {pnl_class}">₹{total_pnl:,.2f}</div>
#                 <div class="kpi-sub">
#                     Return: <span class="{pnl_class}">{total_return_pct}%</span> 
#                     <span class="trend {pnl_class}">{'▲' if total_return_pct >= 0 else '▼'}</span>
#                 </div>
#             </div>

#             <div class="kpi-section medium">
#                 <div class="kpi-title">Funds Invested</div>
#                 <div class="kpi-value">{total_funds}</div>
#             </div>
#         </div>

#     """
    
#     html_output += """
#         <h2>Cap Distribution</h2>"""



#     # Sector Summary Table + Donut Chart
#         # Sector Summary Table + Donut Chart
#     html_output += f"""
#         <div class="top-section">
#             <div class="summary-table">
#                 <table>
#                 <tr>
#                     <th>Sector</th>
#                     <th>Invested Amount (₹)</th>
#                     <th>Expected Distribution (%)</th>
#                     <th>Distribution (%)</th>
#                 </tr>
#     """

    # expected_distribution = {
    #     "Large Cap": 30,
    #     "Mid Cap": 25,
    #     "Small Cap": 25,
    #     "Infrastructure": 15,
    #     "Gold": 5
    # }

    # total_market_value = overall_totals['Market Value'].sum()
    # for _, row in overall_totals.iterrows():
    #     distribution_pct = (row['Market Value'] / total_market_value) * 100
    #     expected_pct = str(expected_distribution.get(row['Sector'], "-")) + "%" if row['Sector'] in expected_distribution else "-"
        
    #     # Swap columns: Expected % comes before Distribution %
    #     html_output += (
    #         f"<tr>"
    #         f"<td>{row['Sector']}</td>"
    #         f"<td>{row['Market Value']:.2f}</td>"
    #         f"<td>{expected_pct}</td>"
    #         f"<td>{distribution_pct:.2f}%</td>"
    #         f"</tr>"
    #     )



#     html_output += f"""
#                 </table>
#             </div>
#             <div class="donut-chart">
#                 <img src="data:image/png;base64,{chart_base64}" alt="Donut Chart">
#             </div>
#         </div>
#     """

#     # Sector-wise breakdown
#     for sector in df['Sector'].unique():
#         html_output += f"<h3>{sector}</h3>"
#         html_output += """
#         <table>
#             <tr>
#                 <th>Scheme Name</th>
#                 <th>Cost Value (₹)</th>
#                 <th>Market Value (₹)</th>
#                 <th>Return (%)</th>
#                 <th>Distribution (%)</th>
#             </tr>
#         """
#         sector_df = df[df['Sector'] == sector].sort_values(by='Distribution %', ascending=False)
#         for _, row in sector_df.iterrows():
#             html_output += f"""
#                 <tr>
#                     <td>{row['Scheme Name']}</td>
#                     <td>{row['Cost Value']}</td>
#                     <td>{row['Market Value']}</td>
#                     <td>{row['Return %']}%</td>
#                     <td>{row['Distribution %']}%</td>
#                 </tr>
#             """
#         html_output += "</table>"

#     # Final AMC Summary (moved to the bottom)
#     html_output += """
#         <h2>AMC Distribution</h2>
#         <table>
#             <tr>
#                 <th>AMC</th>
#                 <th>Invested Amount (₹)</th>
#                 <th>Market Value (₹)</th>
#                 <th>Return (%)</th>
#                 <th>Distribution (%)</th>
#             </tr>
#     """
#     for _, row in amc_totals.iterrows():
#         html_output += f"""
#             <tr>
#                 <td>{row['AMC']}</td>
#                 <td>{row['Cost Value']}</td>
#                 <td>{row['Market Value']}</td>
#                 <td>{row['Return %']}%</td>
#                 <td>{row['Distribution %']}%</td>
#             </tr>
#         """
#     html_output += "</table>"

#     html_output += """
#         <!-- Chatbot Icon -->
#         <div id="chatbot-icon" 
#             style="
#                 position: fixed;
#                 bottom: 20px;
#                 right: 20px;
#                 width: 60px;
#                 height: 60px;
#                 background: linear-gradient(135deg, #1f78b4, #3ba1e3);
#                 border-radius: 50%;
#                 cursor: pointer;
#                 display: flex;
#                 align-items: center;
#                 justify-content: center;
#                 box-shadow: 0 4px 20px rgba(0,0,0,0.2);
#                 z-index: 9999;
#                 transition: transform 0.2s ease;
#             "
#             onmouseover="this.style.transform='scale(1.05)'"
#             onmouseout="this.style.transform='scale(1)'"
#             onclick="toggleChatbot()"
#             title="Open Portfolio Chatbot"
#         >
#             <!-- Chat Bubble SVG Icon -->
#             <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" >
#                 <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
#             </svg>
#         </div>


#         <!-- Chatbot Window -->
#         <div id="chatbot-window" 
#             style="
#                 position: fixed;
#                 bottom: 90px;
#                 right: 20px;
#                 width: 360px;
#                 height: 520px;
#                 background: rgba(255, 255, 255, 0.9);
#                 backdrop-filter: blur(12px);
#                 border-radius: 16px;
#                 box-shadow: 0 8px 32px rgba(0,0,0,0.2);
#                 display: none;
#                 flex-direction: column;
#                 overflow: hidden;
#                 animation: slideUp 0.3s ease forwards;
#                 font-family: Arial, sans-serif;
#                 z-index: 10000;
#             ">
            
#             <!-- Header -->
#             <div style="background: linear-gradient(135deg, #1f78b4, #3ba1e3); 
#                         color: white; padding: 14px; 
#                         font-weight: bold; 
#                         display: flex; justify-content: space-between; align-items: center;">
#                 <span>Portfolio Chatbot</span>
#                 <div style="display: flex; align-items: center; gap: 10px;">
#                     <label class="switch" style="margin: 0; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;">
#                     <input type="checkbox" id="gpt-toggle" />
#                     <span class="slider"></span>
#                     </label>
#                     <span style="font-weight: normal; font-size: 14px;">GPT</span>
#                     <button onclick="toggleChatbot()" 
#                             style="background:none; border:none; color:white; font-size:18px; cursor:pointer; margin-left: 15px;">×</button>
#                 </div>
                
#             </div>


#             <!-- Messages -->
#             <div id="chatbot-messages" 
#                 style="flex: 1; padding: 12px; overflow-y: auto; font-size: 14px;">
#             </div>

#             <!-- Input Area -->
#             <div style="display: flex; flex-direction: column; border-top: 1px solid #ddd; padding: 8px; gap: 6px;">
#                 <div style="display: flex; gap: 6px;">
#                     <input id="chatbot-input" type="text" placeholder="Type your message..." 
#                         style="flex:1; padding: 10px; border-radius: 20px; border: 1px solid #ccc; font-size: 14px;"
#                         onkeypress="if(event.key === 'Enter') sendMessage()" autocomplete="off" />
#                     <button onclick="sendMessage()" 
#                             style="background:#1f78b4; color:white; border:none; padding: 0 15px; 
#                                 border-radius: 20px; cursor: pointer; font-size: 14px;">➤</button>
#                 </div>
#             </div>

#         </div>

#         <!-- Chat Bubble Styles -->
#         <style>

#         label.switch {
#         display: inline-flex !important;
#         align-items: center;
#         gap: 6px;
#         flex-direction: row !important; /* ensures left-to-right layout */
#         }


#         .switch span.slider {
#         order: 1;
#         }
#         .switch span:last-child {
#         order: 2;
#         }

#         .switch {
#         position: relative;
#         display: inline-block;
#         width: 42px;
#         height: 22px;
#         }

#         .switch input {
#         opacity: 0;
#         width: 0;
#         height: 0;
#         }

#         .slider {
#         position: absolute;
#         cursor: pointer;
#         top: 0; left: 0; right: 0; bottom: 0;
#         background-color: #ccc;
#         transition: 0.4s;
#         border-radius: 22px;
#         }

#         .slider:before {
#         position: absolute;
#         content: "";
#         height: 18px;
#         width: 18px;
#         left: 2px;
#         bottom: 2px;
#         background-color: white;
#         transition: 0.4s;
#         border-radius: 50%;
#         }

#         .switch input:checked + .slider {
#         background-color: #1f78b4;
#         }

#         .switch input:checked + .slider:before {
#         transform: translateX(20px);
#         }



#         #chatbot-messages div {
#             max-width: 75%;
#             padding: 10px 14px;
#             border-radius: 12px;
#             margin-bottom: 8px;
#             word-wrap: break-word;
#             line-height: 1.4;
#         }
#         .user-msg {
#             background: #1f78b4;
#             color: white;
#             align-self: flex-end;
#         }
#         .bot-msg {
#             background: #f1f1f1;
#             color: #333;
#             align-self: flex-start;
#         }
#         #chatbot-messages {
#             display: flex;
#             flex-direction: column;
#         }
#         @keyframes slideUp {
#             from { transform: translateY(100%); opacity: 0; }
#             to { transform: translateY(0); opacity: 1; }
#         }

#         .typing-fade {
#             animation: fadeInOut 1.5s infinite;
#             font-style: italic;
#             color: #666;
#             margin-bottom: 8px;
#             }

#             @keyframes fadeInOut {
#             0%, 100% { opacity: 0; }
#             50% { opacity: 1; }
#             }



#         </style>

#         <script>
#         function toggleChatbot() {
#             const win = document.getElementById('chatbot-window');
#             win.style.display = win.style.display === 'flex' ? 'none' : 'flex';
#         }

#         function addMessage(sender, text) {
#             const chatBox = document.getElementById('chatbot-messages');
#             const messageElem = document.createElement('div');
#             messageElem.className = sender === 'You' ? 'user-msg' : 'bot-msg';
#             messageElem.innerHTML = text;
#             chatBox.appendChild(messageElem);
#             chatBox.scrollTop = chatBox.scrollHeight;
#         }

#         async function sendMessage() {
#             const input = document.getElementById('chatbot-input');
#             const chatBox = document.getElementById('chatbot-messages');
#             const msg = input.value.trim();
#             if (!msg) return;

#             // Read GPT toggle status from header toggle
#             const useGPT = document.getElementById('gpt-toggle').checked;

#             addMessage('You', msg);
#             input.value = '';
#             input.disabled = true;

#             // Show bot typing indicator
#             const typingIndicator = document.createElement('div');
#             typingIndicator.className = 'bot-msg typing-fade';
#             typingIndicator.id = 'typing-indicator';
#             typingIndicator.textContent = 'Bot is typing...';
#             chatBox.appendChild(typingIndicator);
#             chatBox.scrollTop = chatBox.scrollHeight;

#             try {
#                 const response = await fetch('/api/chat', {
#                     method: 'POST',
#                     headers: {'Content-Type': 'application/json'},
#                     body: JSON.stringify({message: msg, use_gpt: useGPT})
#                 });
#                 const data = await response.json();

#                 // Remove typing indicator
#                 typingIndicator.remove();

#                 addMessage('Bot', data.response);
#             } catch {
#                 typingIndicator.remove();
#                 addMessage('Bot', '⚠ Unable to connect to the server.');
#             } finally {
#                 input.disabled = false;
#                 input.focus();
#             }
#         }



#         </script>

# """

#     html_output += "</body></html>"
#     return html_output



import pandas as pd
import plotly.graph_objects as go
import base64, io
from io import BytesIO
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker



def prepare_and_generate_html_list(df):
    # ----- Data Preparation -----
    df = df.rename(columns={'Market Cap': 'Sector'})

    df['AMC'] = df['Scheme Name'].str.extract(
        r'(SBI|Nippon|HDFC|ICICI|Motilal|Bandhan|DSP|Franklin|Aditya|Tata|Edelweiss|Invesco|Canara|Mirae|LIC|PGIM|Mahindra|Baroda|Quant)',
        flags=re.IGNORECASE,
        expand=False
    ).str.upper().fillna('OTHER').str.strip()

    df['Return %'] = ((df['Market Value'] - df['Cost Value']) / df['Cost Value']) * 100
    df = df.round({'Market Value': 2, 'Cost Value': 2, 'Return %': 2})

    sector_totals = df.groupby('Sector')['Market Value'].sum().reset_index()
    sector_totals.rename(columns={'Market Value': 'Sector Total'}, inplace=True)
    df = df.merge(sector_totals, on='Sector')
    df['Distribution %'] = round((df['Market Value'] / df['Sector Total']) * 100, 2)

    # Sector ordering
    sector_order = ["Large Cap", "Mid Cap", "Small Cap", "Infrastructure", "Gold", "Tax Saving"]
    df['Sector'] = pd.Categorical(df['Sector'], categories=sector_order, ordered=True)
    overall_totals = df.groupby('Sector')['Market Value'].sum().reset_index().sort_values('Sector')

    df = df.sort_values(['Sector', 'Distribution %'], ascending=[True, False])

    # AMC totals
    amc_totals = (
        df.groupby('AMC')[['Cost Value', 'Market Value']]
        .sum().reset_index()
    )
    amc_totals['Return %'] = ((amc_totals['Market Value'] - amc_totals['Cost Value']) / amc_totals['Cost Value']) * 100
    amc_totals['Distribution %'] = (amc_totals['Market Value'] / amc_totals['Market Value'].sum()) * 100
    amc_totals = amc_totals.round(2).sort_values(by='Market Value', ascending=False)

    # Donut chart
    fig = go.Figure(data=[go.Pie(labels=overall_totals['Sector'],
                                 values=overall_totals['Market Value'],
                                 hole=.5, textinfo='label+percent')])
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    buffer = BytesIO()
    fig.write_image(buffer, format='png')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    # Summary
    total_cost = df['Cost Value'].sum().round(2)
    total_market = df['Market Value'].sum().round(2)
    total_return_pct = (((total_market - total_cost) / total_cost) * 100).round(2)
    total_funds = df['Scheme Name'].nunique()
    total_pnl = total_market - total_cost
    pnl_class = "positive" if total_pnl >= 0 else "negative"


    # Group records by Sector
    df_records = df.to_dict(orient="records")
    cap_wise_funds = defaultdict(list)

    for row in df_records:
        cap = row.get("Sector", "Uncategorized")
        cap_wise_funds[cap].append(row)

    # Optional: enforce sector order
    ordered_cap_wise_funds = {sector: cap_wise_funds.get(sector, []) for sector in sector_order if sector in cap_wise_funds}


    # Pass clean data to template
    return {
        "df": df.to_dict(orient="records"),
        "overall_totals": overall_totals.to_dict(orient="records"),
        "amc_totals": amc_totals.to_dict(orient="records"),
        "total_cost": total_cost,
        "total_market": total_market,
        "total_return_pct": total_return_pct,
        "total_funds": total_funds,
        "total_pnl": total_pnl,
        "pnl_class": pnl_class,
        "chart_base64": chart_base64,
        "cap_wise_funds": ordered_cap_wise_funds
    }




def create_monthly_chart(df):
    """Create a polished, well-balanced monthly investment bar chart with labels."""
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="white")

    df_plot = df.copy()
    df_plot["Month"] = df_plot["Month"].astype(str)

    # Scale y-axis to give labels breathing room
    max_val = df_plot["Total_Investment"].max()
    ax.set_ylim(0, max_val * 1.15)

    # Colors — gradient effect for depth
    bar_color = "#3A7BD5"  # primary blue
    edge_color = "#1F4E79"

    bars = ax.bar(
        df_plot["Month"],
        df_plot["Total_Investment"],
        color=bar_color,
        edgecolor=edge_color,
        linewidth=0.7
    )

    # Title & labels
    ax.set_title("Month-wise Total Investment", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Amount (₹)", fontsize=11)

    # Format Y-axis with commas
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # Gridlines
    ax.grid(axis="y", linestyle="--", linewidth=0.5, color="gray", alpha=0.3)
    ax.set_axisbelow(True)

    # Rotate X-axis labels
    plt.xticks(rotation=40, ha="right")

    # Add value labels with smart positioning
    for bar in bars:
        height = bar.get_height()
        label_y = height + (max_val * 0.015) if height > max_val * 0.05 else height + (max_val * 0.02)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            label_y,
            f"{height:,.0f}",
            ha="center", va="bottom",
            fontsize=9, fontweight="bold",
            color="#222"
        )

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64


