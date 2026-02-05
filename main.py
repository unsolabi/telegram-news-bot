import sys
import os
import feedparser
import anthropic
from urllib.parse import quote
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 1. 파이썬 3.13 호환성 유지 (Mock Class)
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

# [수정] 가장 범용적이고 에러가 없는 모델명으로 교환
MODEL_NAME = "claude-3-haiku-20240307"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 반갑습니다! 주인님의 명령을 최우선으로 수행하는 수석 비서 '항아야'입니다. 무엇이든 명령해 주세요.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # [핵심 판단] 사용자가 '뉴스 검색'을 시켰는지, 아니면 '개인적 지시/대화'인지 판단
        decision_prompt = f"사용자의 메시지가 '실시간 뉴스 검색'을 요청하는 것이면 SEARCH, 그 외 지시나 대화면 DIRECT라고 대답해. 메시지: {user_text}"
        
        check_res = client.messages.create(
            model=MODEL_NAME,
            max_tokens=10,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        decision = check_res.content[0].text.strip().upper()

        if "SEARCH" in decision:
            # 뉴스 검색 모드
            status_msg = await update.message.reply_text(f"🔍 지시하신 '{user_text}' 정보를 분석하고 있습니다...")
            safe_query = quote(user_text)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:3]]
            
            if not news_items:
                await status_msg.edit_text("😢 관련 뉴스를 찾지 못했습니다. 다른 명령을 주시겠어요?")
                return

            analysis_prompt = f"다음 뉴스들을 요약하고 투자 인사이트를 보고해줘:\n\n" + "\n".join(news_items)
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=800,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            await status_msg.edit_text(response.content[0].text)
        
        else:
            # [사용자 지시 우선] 일상 대화 및 개인적 명령 처리
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=800,
                messages=[{"role": "user", "content": f"당신은 70세 투자자의 충성스럽고 유능한 개인 비서 '항아야'입니다. 주인님의 말씀에 정중하고 똑똑하게 답하세요: {user_text}"}]
            )
            await update.message.reply_text(response.content[0].text)

    except Exception as e:
        await update.message.reply_text(f"❌ 비서 가동 중 잠시 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
