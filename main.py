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
        redis_client.lpush(market, json.dumps(report_data))
    except Exception as e:
        print(f"Memory save failed: {e}")

def send_to_slack(report):
    if not SLACK_WEBHOOK_URL: return
    try:
        text = f"""🏢 *ZELUV IO INTELLIGENCE REPORT* 🏢
-----------------------------------
🌍 *Market:* {report.get('market')}
🏠 *Property:* {report.get('property_address', 'N/A')}

📊 *FINANCIAL METRICS:*
• Price: ${report.get('purchase_price', 0):,.0f}
• *Cap Rate:* {report.get('cap_rate', 0)}%
• *Cash-on-Cash ROI:* {report.get('annual_roi_pct', 0)}%
• 1% Rule: {report.get('one_percent_rule', 'N/A')}

⚖️ *LEGAL:* {report.get('legal_risk_level', 'N/A')} Risk

📈 *FORECAST (Agent H):*
• 1Y: {report.get('forecast_1y', 'N/A')} | 3Y: {report.get('forecast_3y', 'N/A')} | 5Y: {report.get('forecast_5y', 'N/A')}

📝 *SUMMARY:*
{report.get('executive_summary', 'N/A')}
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
                print("⏳ [Rate Limit] Pausing 30s...")
                time.sleep(30)
            else:
                print(f"❌ [Groq Error]: {e}")
                return {}

# PROMPTS
PROMPT_A = """[ROLE] You are Agent A. Extract real estate trends.\n[OUTPUT] Output valid JSON: { "status": "SUCCESS", "investment_signal": "string", "emerging_location": "string", "agent_name": "Agent_A" }"""
PROMPT_G = """[ROLE] You are Agent G. Find ONE specific property price.\n[RULES] 1. "purchase_price" MUST be integer. 2. "estimated_monthly_rent" MUST be integer (estimate 0.5% of price if unknown). 3. If no price, output 0.\n[OUTPUT] Output valid JSON: { "property_address": "string", "purchase_price": "integer", "estimated_monthly_rent": "integer", "agent_name": "Agent_G" }"""
PROMPT_C = """[ROLE] You are Agent C, Legal Expert. Check foreign ownership laws.\n[OUTPUT] Output valid JSON: { "legal_compliance": "string", "legal_risk_level": "Low | Medium | High", "agent_name": "Agent_C" }"""
PROMPT_E = """[ROLE] You are Agent E, a CFO.\n[OBJECTIVE] Write a 3-sentence executive summary combining market, financials, and legal.\n[OUTPUT] Output valid JSON: { "executive_summary": "string", "actionable_recommendation": "string", "agent_name": "Agent_E" }"""
PROMPT_H = """[ROLE] You are Agent H, a Portfolio Strategist.\n[OBJECTIVE] Generate a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) and realistic price forecasts (1Y, 3Y, 5Y percentages).\n[OUTPUT] Output valid JSON: { "strengths": "string", "weak
