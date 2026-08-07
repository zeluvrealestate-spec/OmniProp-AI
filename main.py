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

def run_groq_agent(system_prompt, user_prompt):
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
    
    down_pct, int_rate, hoa, tax = 0.20, 0.065, 300, (price * 0.01) / 12
    down_payment = price * down_pct
    loan_amount = price - down_payment
    n, monthly_int = 360, int_rate / 12
    mortgage = loan_amount * (monthly_int * (1 + monthly_int)**n) / ((1 + monthly_int)**n - 1) if monthly_int > 0 else loan_amount / n
    
    monthly_expenses = mortgage + hoa + tax + (rent * 0.15)
    monthly_cashflow = rent - monthly_expenses
    annual_cashflow = monthly_cashflow * 12
    annual_rent = rent * 12
    
    roi = (annual_cashflow / down_payment) * 100 if down_payment > 0 else 0
    cap_rate = (annual_rent / price) * 100 if price > 0 else 0
    one_percent_rule = "PASS" if rent >= (price * 0.01) else "FAIL"
    
    return {
        "purchase_price": price, "down_payment": round(down_payment, 2),
        "monthly_rent": round(rent, 2), "monthly_expenses": round(monthly_expenses, 2),
        "monthly_cashflow": round(monthly_cashflow, 2), "annual_roi_pct": round(roi, 2),
        "cap_rate": round(cap_rate, 2), "one_percent_rule": one_percent_rule
    }

def run_cycle():
    markets = [
        "Dubai apartment for sale price 2026", "Riyadh villa for sale price", 
        "Miami condo for sale price Brickell", "London Canary Wharf apartment for sale",
        "Tokyo Minato ward apartment for sale", "Singapore Orchard condo for sale",
        "New York Manhattan condo for sale", "Berlin Mitte apartment for sale",
        "Sydney Harbourfront apartment for sale", "Paris Le Marais apartment for sale"
    ]
    
    for market in markets:
        print(f"\n{'='*50}\nMARKET: {market.upper()}\n{'='*50}")
        try:
            live_data = deep_search(market)
            if not live_data: 
                send_to_slack({"market": market, "executive_summary": "Agent A could not find any articles for this market."})
                continue
                
            agent_a = run_groq_agent(PROMPT_A, f"Analyze:\n{live_data}")
            if not agent_a: continue
            print(f"✅ [Agent A] Signal: {agent_a.get('investment_signal')}")
            
            agent_g = run_groq_agent(PROMPT_G, f"Extract property:\n{live_data}")
            if not agent_g: continue
            print(f"🏠 [Agent G] Price: ${clean_number(agent_g.get('purchase_price')):,.0f}")
            
            financials = calculate_financials(agent_g)
            if financials:
                print(f"🧮 [Math] ROI: {financials['annual_roi_pct']}% | Cap Rate: {financials['cap_rate']}% | 1% Rule: {financials['one_percent_rule']}")
            else:
                financials = {"purchase_price": 0, "down_payment": 0, "monthly_rent": 0, "monthly_expenses": 0, "monthly_cashflow": 0, "annual_roi_pct": 0, "cap_rate": 0, "one_percent_rule": "N/A"}
                
            agent_c = run_groq_agent(PROMPT_C, f"Check legal:\n{json.dumps(agent_g)}")
            print(f"⚖️ [Agent C] Risk: {agent_c.get('legal_risk_level')}")
            
            agent_e = run_groq_agent(PROMPT_E, f"Market:\n{json.dumps(agent_a)}\nProp:\n{json.dumps(agent_g)}\nFin:\n{json.dumps(financials)}\nLegal:\n{json.dumps(agent_c)}")
            print(f"📝 [Report] {agent_e.get('executive_summary')}")
            
            slack_payload = {
                "market": market, "property_address": agent_g.get('property_address', 'Unknown'),
                "executive_summary": agent_e.get('executive_summary', 'No summary generated.'), 
                "actionable_recommendation": agent_e.get('actionable_recommendation', 'N/A'),
                "purchase_price": financials['purchase_price'], "down_payment": financials['down_payment'],
                "monthly_rent": financials['monthly_rent'], "monthly_expenses": financials['monthly_expenses'],
                "monthly_cashflow": financials['monthly_cashflow'], "annual_roi_pct": financials['annual_roi_pct'],
                "cap_rate": financials['cap_rate'], "one_percent_rule": financials['one_percent_rule'],
                "legal_risk_level": agent_c.get('legal_risk_level', 'N/A'), "legal_compliance": agent_c.get('legal_compliance', 'N/A')
            }
            
            # Save the full payload to Redis for the Dashboard!
            save_report_to_memory(market, slack_payload)
            
            send_to_slack(slack_payload)
            
            time.sleep(15) 
            
        except Exception as e:
            print(f"❌ [MARKET ERROR]: {e}")
            continue

if __name__ == "__main__":
    print("--- OMNIPROP GLOBAL CLOUD WORKER STARTED ---")
    try:
        run_cycle()
        print("\n--- AUTONOMOUS CYCLE COMPLETE ---")
    except Exception as e:
        print(f"❌ [SYSTEM ERROR]: {e}")
