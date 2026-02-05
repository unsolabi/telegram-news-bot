import sys
import os
import feedparser
import anthropic
from urllib.parse import quote
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 1. 파이썬 3.13 호환성 (Mock Class)
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
    await update.message.reply_text("👋 반갑습니다! 주인님의 명령을 최우선으로 수행하는 비서 '항아야'입니다.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # [수정] 모델명을 가장 안정적인 버전으로 교체하여 404 에러 방지
        # 사용자의 의도가 '뉴스 검색'인지 '단순 지시/대화'인지 판단
        decision_prompt = f"""
        사용자의 메시지가 '실시간 뉴스 검색'을 명확히 요청하는 것인지 판단해줘.
        - 뉴스 검색 요청이면: SEARCH
        - 그 외 지시, 질문, 대화면: DIRECT
        메시지: {user_text}
        """
        
        check_res = client.messages.create(
            model="claude-3-sonnet-20240229", # 가장 안정적인 모델로 변경
            max_tokens=10,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        decision = check_res.content[0].text.strip().upper()

        if "SEARCH" in decision:
            status_msg = await update.message.reply_text(f"🔍 지시하신 '{user_text}' 관련 정보를 찾는 중입니다...")
            safe_query = quote(user_text)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:3]]
            
            if not news_items:
                await status_msg.edit_text("😢 관련 뉴스를 찾지 못했습니다. 다른 명령을 주시겠어요?")
                return

            analysis_prompt = f"다음 뉴스들을 요약하고 투자 인사이트를 제공해줘:\n\n" + "\n".join(news_items)
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            await status_msg.edit_text(response.content[0].text)
        
        else:
            # 뉴스 검색이 아닌 모든 지시/대화 처리
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=800,
                messages=[{"role": "user", "content": f"당신은 70세 투자자의 충성스러운 비서 '항아야'입니다. 주인님의 지시나 말에 정중하고 똑똑하게 답하세요: {user_text}"}]
            )
            await update.message.reply_text(response.content[0].text)

    except Exception as e:
        await update.message.reply_text(f"❌ 비서가 잠시 멈췄습니다. (원인: {str(e)})")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
