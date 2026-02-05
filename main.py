import sys
# 1. 최신 파이썬 버전 대응 (Mock Class)
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
    status_msg = await update.message.reply_text(f"🔍 '{user_query}' 관련 뉴스를 실시간으로 검색하여 분석 중입니다...")

    try:
        # 뉴스 검색 (RSS 활용)
        rss_url = f"https://news.google.com/rss/search?q={user_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:5]]
        news_text = "\n".join(news_items)

        if not news_items:
            await status_msg.edit_text("😢 관련 최신 뉴스를 찾지 못했습니다. 다른 키워드로 검색해 볼까요?")
            return

        # 클로드 AI에게 분석 요청
        prompt = f"다음은 '{user_query}'와 관련된 최신 뉴스들입니다. 핵심 내용을 요약하고 투자자에게 도움될 인사이트를 제공해줘:\n\n{news_text}"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        final_answer = response.content[0].text
        await status_msg.edit_text(final_answer)

    except Exception as e:
        await status_msg.edit_text(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
