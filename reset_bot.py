import requests
import time

# 봇 토큰
token = "8565522116:AAEBRSHfxYs1YwdFHuT8Bd6ocs5QGjKihsg"

print("=" * 50)
print("🔧 텔레그램 봇 웹훅 리셋")
print("=" * 50)
print()

# 웹훅 삭제
print("⏳ 웹훅 삭제 중...")
url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"

try:
    response = requests.get(url)
    result = response.json()
    
    if result.get("ok"):
        print("✅ 웹훅 삭제 성공!")
        print()
        print("5초 후 봇을 다시 실행하세요:")
        print("py -3.11 main.py")
        print()
        
        # 카운트다운
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        
        print()
        print("✨ 준비 완료! 이제 봇을 실행하세요!")
    else:
        print("❌ 에러:", result)
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")

print()
input("엔터를 눌러 종료...")
