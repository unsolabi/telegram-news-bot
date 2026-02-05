import sys
# 1. 파이썬 3.13 대응 (Mock Class 설정)
try:
    import cgi
except ImportError:
    import html
    class MockCgi:
        escape = html.escape
    sys.modules['cgi'] = MockCgi

import os
import feedparser
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 환경 변수 설정
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 반갑습니다! 실시간 뉴스 분석 비서입니다. 궁금하신 종목이나 주제를 말씀해 주세요.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    status_msg = await update.message.reply_text(f"🔍 '{user_query}' 뉴스를 분석 중입니다. 잠시만 기다려 주세요...")

    try:
        # 1. 뉴스 검색
        rss_url = f"https://news.google.com/rss/search?q={user_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:5]]
        news_text = "\n".join(news_items)

        if not news_items:
            await status_msg.edit_text("😢 관련 최신 뉴스를 찾지 못했습니다.")
            return

        # 2. 클로드 AI에게 분석 요청 (모델명 수정 완료)
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
