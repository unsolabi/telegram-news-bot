import sys
import os
import feedparser
import anthropic
from urllib.parse import quote
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
    await update.message.reply_text("👋 반갑습니다! 당신의 유능한 투자 비서 '항아야'입니다. 궁금한 종목 분석이나 실시간 뉴스를 물어봐 주시고, 일상적인 대화도 언제든 환영합니다.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # [핵심 로직] 클로드에게 사용자 의도 파악 요청
        # 오류를 줄이기 위해 판단 기준을 명확히 제시했습니다.
        decision_prompt = f"""
        사용자의 메시지를 분석해서 다음 중 하나로 응답해줘.
        - 'SEARCH': 특정 종목, 경제 지표, 시사 뉴스 등 실시간 정보 검색이 필요한 경우
        - 'CHAT': 단순 인사, 감정 표현, 일상적인 대화, 또는 비서의 태도에 대한 피드백인 경우
        
        메시지: "{user_text}"
        결과(SEARCH 또는 CHAT):
        """
        
        check_res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        decision = check_res.content[0].text.strip().upper()

        # 2. 뉴스 검색 모드
        if "SEARCH" in decision:
            status_msg = await update.message.reply_text(f"🔍 '{user_text}'에 대한 최신 뉴스를 수집하여 분석 중입니다...")
            
            safe_query = quote(user_text)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:5]]
            
            if not news_items:
                await status_msg.edit_text("😢 관련 최신 뉴스를 찾지 못했습니다. 키워드를 조금 바꿔서 다시 말씀해 주시겠어요?")
                return

            analysis_prompt = f"당신은 투자 전문가입니다. 다음 뉴스들을 요약하고 투자자에게 유용한 인사이트를 제공해줘:\n\n" + "\n".join(news_items)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            await status_msg.edit_text(response.content[0].text)
        
        # 3. 일상 대화 모드
        else:
            chat_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user", 
                    "content": f"당신은 70세 투자자의 다정하고 지혜로운 개인 비서 '항아야'입니다. 격식 있으면서도 따뜻한 말투로 대답해 주세요: {user_text}"
                }]
            )
            await update.message.reply_text(chat_response.content[0].text)

    except Exception as e:
        await update.message.reply_text(f"❌ 비서 가동 중 잠시 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
