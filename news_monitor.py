import feedparser
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher
import urllib.parse

# ==============================
# 🔑 이메일 설정
# ==============================

sender_email = "huinews91@gmail.com"
sender_password = "jlxraulcdqugnwox"

receiver_emails = [
    "inkwunheo@chungho.com",
    "matt633@chungho.com",
    "dorosi7876@chungho.com",
    "jane@chungho.com",
    "jjw@chungho.com",
    "hui0901@chungho.com",
    "gpdmswh@naver.com"
]

# ==============================
# 📰 뉴스 카테고리 + 키워드
# ==============================

categories = {

     "청호나이스 관련 뉴스": [
        "청호나이스"
    ],
    
    "경쟁사 관련 뉴스": [
        "코웨이",
        "SK인텔릭스",
        "LG전자",
        "삼성전자",
        "쿠쿠",
        "교원웰스",
        "현대렌탈"
    ],

    "제품 관련 뉴스": [
        "정수기",
        "얼음정수기",
        "커피머신",
        "비데",
        "연수기",
        "매트리스",
        "공기청정기",
        "음식물 쓰레기 처리기",
        "안마의자",
        "가습기",
        "제습기"
    ],

    "가전 관련 뉴스": [
        "렌탈가전",
        "가전 구독",
        "환경가전",
        "생활가전",
        "주방가전"
    ]

}

# ==============================
# 🚫 차단 소스
# ==============================

blocked_sources = [
    "블로그",
    "카페",
    "티스토리",
    "브런치",
    "포스트",
    "유튜브"
]

def is_blocked(source):

    for blocked in blocked_sources:
        if blocked.lower() in source.lower():
            return True

    return False


# ==============================
# ⭐ 신제품 우선
# ==============================

priority_words = [
    "신제품",
    "출시",
    "런칭",
    "신형",
    "공개"
]

def is_priority(title):

    for word in priority_words:
        if word in title:
            return True

    return False


# ==============================
# 🔁 제목 중복 제거
# ==============================

def normalize(text):

    text=re.sub(r'\[.*?\]','',text)
    text=re.sub(r'[^\w\s]','',text)
    text=text.replace(" ","")

    return text.lower()


def is_similar(title,seen_titles):

    norm_title=normalize(title)

    for seen in seen_titles:

        similarity=SequenceMatcher(None,norm_title,seen).ratio()

        if similarity>0.85:
            return True

    return False


# ==============================
# 📰 뉴스 수집
# ==============================

def get_news(keyword,days_limit):

    encoded_keyword = urllib.parse.quote(keyword)

    url=f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"

    feed=feedparser.parse(url)

    today=datetime.now()

    priority_list=[]
    normal_list=[]

    for entry in feed.entries:

        if not hasattr(entry,"published_parsed"):
            continue

        published=datetime(*entry.published_parsed[:6])

        if today-published>timedelta(days=days_limit):
            continue

        title=entry.title
        link=entry.link

        source=entry.source.title if hasattr(entry,"source") else "출처미상"

        if is_blocked(source):
            continue

        news_item=(title,link,source)

        if is_priority(title):
            priority_list.append(news_item)
        else:
            normal_list.append(news_item)

    combined=priority_list+normal_list

    return combined[:5]


# ==============================
# 📧 이메일 발송 (HTML + 클릭링크)
# ==============================

def send_email(html_content):

    today=datetime.now().strftime("%Y-%m-%d")

    msg=MIMEText(html_content,"html","utf-8")

    msg["Subject"]=f"[뉴스 모니터]{today}"

    msg["From"]=sender_email
    msg["To"]=", ".join(receiver_emails)

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:

        server.login(sender_email,sender_password)

        server.send_message(msg)


# ==============================
# 🧠 메인 실행
# ==============================

def main():

    today=datetime.now()

    if today.weekday()==0:
        days_limit=4
    else:
        days_limit=2


    html="""

    <html>
    <body style="font-family:맑은고딕;">

    """

    html+=f"<h2>뉴스 모니터링 ({today.strftime('%Y-%m-%d')})</h2>"


    global_seen_titles=[]


    for category,keywords in categories.items():

        html+=f"<h3 style='background-color:#eeeeee;padding:8px;'>{category}</h3>"


        for keyword in keywords:

            news_list=get_news(keyword,days_limit)

            html+=f"<b>{keyword}</b><br><br>"


            if not news_list:

                html+="기사 없음<br><br>"
                continue


            count=1

            for title,link,source in news_list:

                if is_similar(title,global_seen_titles):
                    continue

                html+=f"{count}. <a href='{link}'>{title}</a><br>"
                html+=f"출처: {source}<br><br>"

                global_seen_titles.append(normalize(title))

                count+=1

                if count>5:
                    break


    html+="</body></html>"


    send_email(html)

    print("메일 발송 완료")


if __name__=="__main__":
    main()
