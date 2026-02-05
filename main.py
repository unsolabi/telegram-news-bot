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

# 가장 안정적인 모델 고정
MODEL_NAME = "claude-3-haiku-20240307"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 반갑습니다! 주인님의 명령을 최우선으로 수행하는 비서 '항아야'입니다. 무엇을 도와드릴까요?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # [강력 지침] 비서에게 '정직함' 원칙 주입
        system_instruction = """
        당신은 70세 투자자 주인님의 전담 비서 '항아야'입니다.
        1. 당신은 현재 주인님의 구글 일정, 캘린더, 메모장에 접근할 권한이 전혀 없습니다.
        2. "오늘 일정 알려줘"와 같은 질문에 절대 가상의 회의나 식사 약속을 지어내지 마세요.
        3. 일정을 물어보면 "주인님, 제가 아직 외부 데이터를 읽을 권한이 없어 실제 일정을 확인할 수 없습니다"라고 솔직하게 보고하세요.
        4. 오직 주인님이 직접 지시한 실시간 뉴스 검색(SEARCH)이나 일반 대화에만 응하세요.
        """

        # 의도 파악
        decision_prompt = f"{system_instruction}\n\n사용자의 메시지가 '실시간 뉴스 검색' 요청이면 SEARCH, 아니면 DIRECT라고 대답해: {user_text}"
        
        check_res = client.messages.create(
            model=MODEL_NAME,
            max_tokens=10,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        decision = check_res.content[0].text.strip().upper()

        if "SEARCH" in decision:
            status_msg = await update.message.reply_text("🔍 지시하신 내용을 바탕으로 뉴스를 분석 중입니다...")
            safe_query = quote(user_text)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:3]]
            
            if not news_items:
                await status_msg.edit_text("😢 관련 정보를 찾지 못했습니다. 다른 키워드로 명령해 주세요.")
                return

            analysis_prompt = f"{system_instruction}\n\n다음 뉴스들을 요약 보고해줘:\n\n" + "\n".join(news_items)
            response = client.messages.create(
                model=MODEL_NAME, max_tokens=800,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            await status_msg.edit_text(response.content[0].text)
        
        else:
            # 일상 대화 및 지시 처리
            response = client.messages.create(
                model=MODEL_NAME, max_tokens=800,
                messages=[{"role": "user", "content": f"{system_instruction}\n\n주인님의 말씀입니다: {user_text}"}]
            )
            await update.message.reply_text(response.content[0].text)

    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
