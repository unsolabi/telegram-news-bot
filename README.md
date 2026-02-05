# 📡 Telegram News Bot + AI Assistant

Telegram 봇으로 최신 뉴스를 받고 Claude AI와 자유로운 대화를 나눌 수 있습니다!

## ✨ 기능

- 📰 **실시간 뉴스 조회**: /news 명령어로 최신 뉴스 5개 받기
- 🤖 **AI 개인비서**: Claude AI와 자유로운 대화
- 💬 **일반 대화**: 뭐든 물어볼 수 있습니다
- 📖 **도움말**: /help 명령어

## 🚀 설치 및 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/telegram-news-bot.git
cd telegram-news-bot
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. API 키 설정

#### Windows (명령 프롬프트)
```cmd
set TELEGRAM_TOKEN=your_telegram_bot_token_here
set CLAUDE_API_KEY=your_claude_api_key_here
python main.py
```

#### macOS / Linux (터미널)
```bash
export TELEGRAM_TOKEN=your_telegram_bot_token_here
export CLAUDE_API_KEY=your_claude_api_key_here
python main.py
```

#### .env 파일 사용 (선택사항)
```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 토큰 입력
# 그 다음 실행
python main.py
```

## 📋 필수 API 키 획득 방법

### Telegram Bot Token 받기
1. Telegram에서 @BotFather를 찾아 채팅 시작
2. `/newbot` 명령어 입력
3. 봇 이름과 사용자명 입력
4. 받은 토큰 복사

### Claude API Key 받기
1. https://console.anthropic.com 접속
2. 로그인 (없으면 가입)
3. API Keys 섹션에서 "Create Key" 클릭
4. 생성된 키 복사

## 📝 사용 예시

### 텔레그램에서 봇과 대화

```
사용자: /start
봇: 안녕하세요! 📡 뉴스 브리핑 + AI 개인비서 봇입니다!

사용자: /news
봇: 📰 뉴스 수집 중...
(최신 뉴스 5개 표시)

사용자: 파이썬 배우려면 어떻게 해?
봇: 파이썬을 배우기 위한 여러 방법이 있습니다...
(Claude AI가 답변)

사용자: /help
봇: 📖 도움말 표시
```

## 🛠️ 프로젝트 구조

```
telegram-news-bot/
├── main.py              # 메인 봇 파일
├── requirements.txt     # 필요한 패키지
├── .env.example         # 환경변수 예제
└── README.md            # 이 파일
```

## ⚙️ 사용된 기술

- **python-telegram-bot**: Telegram Bot API
- **anthropic**: Claude AI API
- **feedparser**: RSS 뉴스 피드 파싱
- **requests & BeautifulSoup**: 웹 크롤링

## 🔧 커스터마이징

### RSS 뉴스 소스 추가
main.py의 `RSS_FEEDS` 리스트에 새로운 피드 URL 추가:

```python
RSS_FEEDS = [
    "https://www.mk.co.kr/rss/30100041/",
    "https://your-new-feed-url.com/rss",  # 새로 추가
]
```

### AI 모델 변경
main.py의 `get_ai_response()` 함수에서 모델명 변경:

```python
model="claude-3-5-sonnet-20241022",  # 다른 모델로 변경 가능
```

## 📞 문제 해결

### "TELEGRAM_TOKEN이 설정되지 않았습니다" 에러
- 위의 "3. API 키 설정" 부분을 다시 확인하세요
- 토큰을 올바르게 설정했는지 확인하세요

### Claude API 오류
- CLAUDE_API_KEY가 올바른지 확인하세요
- API 키의 주기가 만료되지 않았는지 확인하세요
- Anthropic 대시보드에서 API 사용량을 확인하세요

### 뉴스가 안 나옴
- 인터넷 연결을 확인하세요
- RSS 피드 URL이 정상 작동하는지 확인하세요

## 📄 라이선스

MIT License

## 👨‍💻 기여

버그 리포트나 개선 사항은 Issue 또는 Pull Request로 제출해주세요!

## 🎯 향후 개선 예정

- [ ] 데이터베이스에 사용자 대화 저장
- [ ] 다국어 지원
- [ ] 이미지 검색 기능
- [ ] 사용자별 뉴스 선호도 설정
- [ ] 정기 뉴스 알림

---

**Made with ❤️ using Claude AI**
