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
    await update.message.reply_text("👋 반갑습니다! 주인님의 명령을 최우선으로 수행하는 비서 '항아야'입니다. 무엇을 도와드릴까요?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # [핵심 로직] 사용자 지시 우선 판단
        decision_prompt = f"""
        사용자의 메시지를 보고 다음 중 하나로 엄격하게 판단해줘.
        - 'SEARCH': 사용자가 명확하게 "~뉴스 찾아줘", "~검색해줘", "~최신 소식 알려줘" 등 실시간 정보 검색을 '명령'했을 때만.
        - 'DIRECT': 그 외 모든 경우. (인사, 질문, 개인적인 지시, 일상 대화 등)
        
        메시지: "{user_text}"
        결과(SEARCH 또는 DIRECT):
        """
        
        check_res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": decision_prompt}]
        )
        
        decision = check_res.content[0].text.strip().upper()

        # 2. 뉴스 검색 명령을 받았을 때만 가동
        if "SEARCH" in decision:
            status_msg = await update.message.reply_text("🔍 지시하신 내용을 바탕으로 최신 정보를 수집하고 있습니다...")
            
            safe_query = quote(user_text)
            rss_url = f"https://news.google.com/rss/search?q={safe_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            news_items = [f"제목: {entry.title} / 링크: {entry.link}" for entry in feed.entries[:5]]
            
            if not news_items:
                await status_msg.edit_text("😢 관련 뉴스를 찾지 못했습니다. 키워드를 바꿔서 다시 명령해 주시겠습니까?")
                return

            analysis_prompt = f"투자 전문가의 시각으로 다음 뉴스들을 요약하고 핵심 인사이트를 보고해줘:\n\n" + "\n".join(news_items)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            await status_msg.edit_text(response.content[0].text)
        
        # 3. 사용자 지시 및 일반 대화 (이 부분이 메인이 됩니다)
        else:
            chat_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{
                    "role": "user", 
                    "content": f"당신은 70세 투자자의 아주 유능하고 충성스러운 개인 비서 '항아야'입니다. 주인님의 말씀에 귀를 기울이고, 지시하신 사항을 우선적으로 처리하며 답변해 주세요: {user_text}"
                }]
            )
            await update.message.reply_text(chat_response.content[0].text)

    except Exception as e:
        await update.message.reply_text(f"❌ 비서 가동 중 오류가 발생했습니다: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()
