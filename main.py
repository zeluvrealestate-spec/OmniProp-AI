import os
import groq
import json
import requests
import redis
import datetime
import time
from tavily import TavilyClient

# ==========================================
# CONFIGURATION
# ==========================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
REDIS_URL = os.environ.get("REDIS_URL", "redis://red-d9q7dsfavr4c73av0fcg:6379")

client = groq.Groq(api_key=GROQ_API_KEY)

print("[Initializing Cloud Memory (Redis)...]")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("✅ Redis Connected!")
except Exception as e:
    print(f"❌ Redis Error: {e}")
    redis_client = None

def save_report_to_memory(market, report_data):
    if not redis_client: return
    try:
        report_id = f"{market}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        # Save the entire dictionary as a JSON string so the dashboard can read it
        redis_client.lpush(market, json.dumps(report_data))
    except Exception as e:
        print(f"Memory save failed: {e}")

def send_to_slack(report):
    if not SLACK_WEBHOOK_URL:
        print("❌ [Slack Error]: SLACK_WEBHOOK_URL secret is missing!")
        return
    try:
        text = f"""🏢 *GLOBAL INVESTMENT INTELLIGENCE REPORT* 🏢
-----------------------------------
🌍 *Market:* {report.get('market')}
🏠 *Property:* {report.get('property_address', 'N/A')}

📊 *FINANCIAL METRICS:*
• Purchase Price: ${report.get('purchase_price', 0):,.0f}
• Down Payment (20%): ${report.get('down_payment', 0):,.0f}
• Monthly Rent: ${report.get('monthly_rent', 0):,.0f}
• Monthly Expenses: ${report.get('monthly_expenses', 0):,.0f}
• *Monthly Cash Flow: ${report.get('monthly_cashflow', 0):,.2f}*
• *Cap Rate:* {report.get('cap_rate', 0)}%
• *Cash-on-Cash Return:* {report.get('annual_roi_pct', 0)}%
• *1% Rule:* {report.get('one_percent_rule', 'N/A')}

⚖️ *LEGAL & REGULATORY:*
• Risk Level: {report.get('legal_risk_level', 'N/A')}
• Compliance: {report.get('legal_compliance', 'N/A')}

📝 *EXECUTIVE SUMMARY:*
{report.get('executive_summary', 'N/A')}

💡 *RECOMMENDATION:*
{report.get('actionable_recommendation', 'N/A')}
-----------------------------------"""
        
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": text})
        print(f"📱 [SLACK SENT] Status: {response.status_code}")
    except Exception as e:
        print(f"❌ [Slack Error]: {e}")

def deep_search(query):
    print(f"\n[Agent A searching: '{query}'...]")
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily.search(query=query, max_results=1, include_raw_content=True)
        if response and isinstance(response, dict) and response.get('results'):
            full_text = response['results'][0].get('raw_content') or response['results'][0].get('content', '')
            if full_text: return full_text[:3000]
        return None
    except Exception as e:
        print(f"❌ [Tavily Error]: {e}")
        return None

# ==========================================
# GROQ AI ENGINE (With Retry Logic)
# ==========================================
def run_groq_agent(system_prompt, user_prompt):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.7
            )
            content = chat_completion.choices[0].message.content
            return json.loads(content) if content else {}
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print("⏳ [Rate Limit Reached] Pausing for 30 seconds to let Groq reset...")
                time.sleep(30)
            else:
                print(f"❌ [Groq Error]: {e}")
                return {}

PROMPT_A = """[ROLE] You are Agent A. Extract real estate trends.\n[OUTPUT] Output valid JSON: { "status": "SUCCESS", "investment_signal": "string", "emerging_location": "string", "agent_name": "Agent_A" }"""
PROMPT_G = """[ROLE] You are Agent G. Find ONE specific property price.\n[RULES] 1. "purchase_price" MUST be integer. 2. "estimated_monthly_rent" MUST be integer (estimate 0.5% of price if unknown). 3. If no price, output 0.\n[OUTPUT] Output valid JSON: { "property_address": "string", "purchase_price": "integer", "estimated_monthly_rent": "integer", "agent_name": "Agent_G" }"""
PROMPT_C = """[ROLE] You are Agent C, Legal Expert. Check foreign ownership laws for the location.\n[OUTPUT] Output valid JSON: { "legal_compliance": "string", "legal_risk_level": "Low | Medium | High", "agent_name": "Agent_C" }"""
PROMPT_E = """[ROLE] You are Agent E, a Chief Financial Officer (CFO).\n[OBJECTIVE] Write a 4-sentence executive summary combining market, financials (Cap Rate, 1% Rule), and legal.\n[OUTPUT] Output valid JSON: { "executive_summary": "string", "actionable_recommendation": "string", "agent_name": "Agent_E" }"""

def clean_number(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        clean_val = val.replace(',', '').replace('$', '').strip().lower()
        if 'k' in clean_val: return float(clean_val.replace('k', '')) * 1000
        if 'm' in clean_val: return float(clean_val.replace('m', '')) * 1000000
        try: return float(clean_val)
        except ValueError: return 0
    return 0

def calculate_financials(financials):
    if not financials: return None
    price = clean_number(financials.get('purchase_price', 0))
    rent = clean_number(financials.get('estimated_monthly_rent', 0))
    if price == 0: return None
    if rent > (price * 0.01) or rent == 0: rent = price * 0.005
    
    down_pct, int_rate, hoa, tax = 0.20, 0.065, 300, (price * 0.01) /
