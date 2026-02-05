import os
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import anthropic

# -------- 설정 --------
logging.basicConfig(level=logging.INFO)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Claude 클라이언트 초기화
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# -------- RSS 뉴스 소스 --------
RSS_FEEDS = [
    "https://www.mk.co.kr/rss/30100041/",   # 한국 경제
    "https://rss.donga.com/total.xml",     # 한국 종합
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # 미국 경제
    "http://feeds.bbci.co.uk/news/world/rss.xml",     # 세계 뉴스
]

# -------- 기사 본문 일부 가져오기 --------
def get_article_text(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs[:5])
        return text[:800]
    except:
        return ""

# -------- 뉴스 수집 --------
def fetch_news():
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                title = entry.title
                link = entry.link
                content = get_article_text(link)
                articles.append((title, link, content))
        except:
            continue
    return articles[:5]

# -------- 뉴스 요약 --------
def summarize(title, content):
    if not content:
        return f"📰 {title}\n(본문 요약 불가)"
    return f"📰 {title}\n요약: {content[:200]}..."

# -------- Claude API로 대화 응답 생성 --------
def get_ai_response(user_message):
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        logging.error(f"Claude API 에러: {e}")
        return "죄송합니다. 응답을 생성할 수 없습니다."

# -------- /start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! 📡 뉴스 브리핑 + AI 개인비서 봇입니다!\n\n"
        "사용 가능한 명령어:\n"
        "/news - 최신 뉴스 조회\n"
        "/help - 도움말\n\n"
        "일반 대화도 자유롭게 나눌 수 있습니다! 😊"
    )

# -------- /help --------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 도움말\n\n"
        "이 봇은 다음 기능을 제공합니다:\n\n"
        "1️⃣ /news - 최신 뉴스 5개 조회\n"
        "2️⃣ 일반 질문 - AI가 대답해줍니다\n"
        "   예: '날씨 어때?', '파이썬 배우려면?'\n"
        "3️⃣ /start - 시작 메시지"
    )

# -------- /news --------
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 뉴스 수집 중...")
    articles = fetch_news()
    if not articles:
        await update.message.reply_text("오늘 주요 뉴스를 가져오지 못했습니다.")
        return
    for title, link, content in articles:
        summary = summarize(title, content)
        await update.message.reply_text(f"{summary}\n🔗 {link}")

# -------- 일반 대화 (개선됨) --------
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # 입력 중 표시
    await update.message.chat.send_action("typing")
    
    # AI 응답 생성
    ai_response = get_ai_response(user_message)
    
    # 응답 전송 (길면 여러 메시지로 분할)
    if len(ai_response) > 4096:
        for i in range(0, len(ai_response), 4096):
            await update.message.reply_text(ai_response[i:i+4096])
    else:
        await update.message.reply_text(ai_response)

# -------- 오류 처리 --------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

# -------- 봇 실행 --------
def main():
    if not TELEGRAM_TOKEN:
        print("❌ 에러: TELEGRAM_TOKEN이 설정되지 않았습니다.")
        print("다음 명령어로 설정하세요:")
        print('export TELEGRAM_TOKEN="your_token_here"')
        return
    
    if not CLAUDE_API_KEY:
        print("❌ 에러: CLAUDE_API_KEY가 설정되지 않았습니다.")
        print("다음 명령어로 설정하세요:")
        print('export CLAUDE_API_KEY="your_api_key_here"')
        return
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # 핸들러 추가
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_error_handler(error_handler)
    
    print("✅ 봇 시작 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
