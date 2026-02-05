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

# 로깅 설정
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 환경 변수 가져오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 안녕하세요! 실시간 뉴스 검색 비서입니다. 궁금하신 뉴스 주제를 말씀해 주세요.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # 비서가 응답을 준비 중이라는 메시지
    await update.message.reply_text(f"🔍 '{user_text}'에 대한 뉴스를 분석 중입니다. 잠시만 기다려 주세요...")
    
    # 여기에 뉴스 검색 및 클로드 분석 로직이 들어갑니다.
    # (현재는 연결 테스트를 위해 간단한 응답만 보냅니다.)
    await update.message.reply_text(f"✅ 요청하신 '{user_text}' 관련 뉴스 검색 기능이 정상 가동 중입니다!")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not ANTHROPIC_API_KEY:
        print("❌ 필수 토큰(TELEGRAM_TOKEN 또는 ANTHROPIC_API_KEY)이 없습니다.")
        sys.exit(1)

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 실시간 검색 비서가 시작되었습니다.")
    application.run_polling()
