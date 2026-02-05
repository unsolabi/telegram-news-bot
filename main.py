import sys
try:
    import cgi
except ImportError:
    import html
    import http.cookies
    class MockCgi:
        escape = html.escape
        parse = None
    sys.modules['cgi'] = MockCgi



import os
import logging
import feedparser
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# -------- 1. 설정 (Railway 환경변수 로드) --------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Railway의 Variables 탭에 입력한 값을 가져옵니다.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 토큰이 없을 경우 에러 방지
if not TELEGRAM_TOKEN or not CLAUDE_API_KEY:
    logging.error("❌ 필수 토큰(TELEGRAM_TOKEN 또는 ANTHROPIC_API_KEY)이 설정되지 않았습니다.")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# -------- 2. 실시간 뉴스 검색 함수 --------
def fetch_realtime_news():
    """공신력 있는 매일경제, 동아일보의 실시간 RSS 뉴스를 가져옵니다."""
    feeds = [
        "https://www.mk.co.kr/rss/30100041/", # 매일경제 경제
        "https://rss.donga.com/total.xml"      # 동아일보 전체
    ]
    news_results = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # 각 매체당 최신글 3개씩
                news_results.append(f"제목: {entry.title}\n요약: {entry.description[:100]}...")
        except: continue
    return "\n\n".join(news_results) if news_results else "현재 실시간 뉴스 검색 결과를 가져올 수 없습니다."

# -------- 3. 비서의 대답 로직 --------
def get_ai_response(user_text):
    current_news = fetch_realtime_news()
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=(
                "당신은 70세 사용자님을 모시는 정중한 '수석 비서'입니다.\n"
                "사용자님은 재테크(VOO, SCHD), 파이썬, 실리콘 배합에 관심이 많습니다.\n\n"
                "**필독 규칙:**\n"
                f"1. 아래 제공되는 [실시간 뉴스 정보]에 근거해서만 시사/경제 답변을 하십시오.\n"
                "2. 본인이 모르는 주가나 지수를 절대로 추측해서 숫자로 말하지 마십시오.\n"
                "3. 검색 결과에 없는 내용은 반드시 '실시간 확인이 필요하여 지금은 정확히 알 수 없습니다'라고 정직하게 말하십시오.\n"
                "4. 항상 정중하고 명확하게 답변하십시오.\n\n"
                f"[실시간 뉴스 정보]:\n{current_news}"
            ),
            messages=[{"role": "user", "content": user_text}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ 비서가 응답에 실패했습니다. (원인: {type(e).__name__})"

# -------- 4. 실행 부분 --------
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("수석 비서가 실시간 뉴스 검색 기능을 탑재하고 가동되었습니다. 무엇이든 물어봐 주십시오.")

async def handle_message(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.chat.send_action("typing")
    reply = get_ai_response(u.message.text)
    await u.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 실시간 검색 비서가 시작되었습니다.")
    app.run_polling()
