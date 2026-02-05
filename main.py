import sys
import os
import feedparser
import anthropic
from urllib.parse import quote  # 공백 및 특수문자 변환용 도구 추가
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 1. 파이썬 3.13 대응 (Mock Class 설정)
try:
    import cgi
except ImportError:
    import html
    class MockCgi:
        escape = html.escape
    sys.modules['cgi'] = MockCgi

# 환경 변수 설정
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 반갑습니다! 실시간 뉴스 분석 비서입니다. 궁금하신 종목이나 주제를 말씀해 주세요.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    status_msg = await update.message.reply_text(f"🔍 '{user_query}' 뉴스를 실시간으로 분석 중입니다...")

    try:
        # 2. 검색어 인코딩 (공백 에러 해결의 핵심)
        # 검색어 내의 공백을 인터넷 주소용 문자로 변환합니다.
        safe_query = quote(user_query)
        rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        # 3. 뉴스 검색
        feed = feedparser.parse(rss_url)
        news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:5]]
        news_text = "\n".join(news_items)

        if not news_items:
            await status_msg.edit_text("😢 관련 최신 뉴스를 찾지 못했습니다. 다른 검색어로 시도해 보세요.")
            return

        # 4. 클로드 AI에게 분석 요청
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": f"다음 뉴스들을 요약하고 투자 인사이트를 제공해줘:\n\n{news_text}"}]
        )
        
        await status_msg.edit_text(response.content[0].text)

    except Exception as e:
        await status_msg.edit_text(f"❌ 오류 발생: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
