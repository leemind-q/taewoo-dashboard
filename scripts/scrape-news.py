#!/usr/bin/env python3
"""
네이버 뉴스 스크래퍼 — IT/과학, 반도체, AI 3카테고리
GitHub Actions에서 실행 → news.json 생성 → 자동 커밋
의존성: 없음 (표준 라이브러리만 사용)
"""
import urllib.request, urllib.parse, re, json, sys, os
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='replace')

def scrape_section(section_id):
    """네이버 뉴스 섹션 페이지 스크래핑 (section_id: 105=IT/과학)"""
    url = f'https://news.naver.com/section/{section_id}'
    html = fetch_html(url)

    # sa_item 블록에서 제목과 링크 쌍 추출
    pattern = r'<a href="(https://n\.news\.naver\.com/mnews/article/[^"]+)"[^>]*class="sa_text_title"[^>]*>.*?<strong class="sa_text_strong"[^>]*>([^<]+)</strong>'
    matches = re.findall(pattern, html, re.DOTALL)

    if not matches:
        # 폴백 패턴
        titles = re.findall(r'<strong class="sa_text_strong"[^>]*>([^<]+)</strong>', html)
        links = re.findall(r'href="(https://n\.news\.naver\.com/mnews/article/[^"]+)"', html)
        matches = list(zip(links, titles))

    # 중복 제거
    seen = set()
    articles = []
    for link, title in matches:
        if link not in seen:
            seen.add(link)
            title = title.strip()
            # HTML 엔티티 정리
            title = title.replace('&#x27;', "'").replace('&quot;', '"').replace('&amp;', '&')
            articles.append({'title': title, 'link': link, 'source': '네이버 뉴스'})
    return articles[:5]

def scrape_search(query):
    """네이버 뉴스 검색 결과 스크래핑"""
    url = f'https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(query)}&sort=1&nso=so:dd,p:all'
    html = fetch_html(url)

    # 검색 결과의 뉴스 타이틀과 링크 추출
    pattern = r'<a class="news_t"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html)

    if not matches:
        # 대체 패턴
        pattern2 = r'href="(https://n\.news\.naver\.com[^"]+)"[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)'
        matches = re.findall(pattern2, html)

    if not matches:
        # 또 다른 패턴
        pattern3 = r'title="([^"]+)"[^>]*href="(https://n\.news\.naver\.com[^"]+)"'
        matches2 = re.findall(pattern3, html)
        matches = [(link, title) for title, link in matches2]

    seen = set()
    articles = []
    for link, title in matches:
        if 'n.news.naver.com' in link and link not in seen:
            seen.add(link)
            title = title.strip()
            title = title.replace('&#x27;', "'").replace('&quot;', '"').replace('&amp;', '&')
            articles.append({'title': title, 'link': link, 'source': '네이버 뉴스'})
    return articles[:5]

def scrape_google_news(query):
    """Google News RSS 폴백 (네이버 스크래핑 실패 시)"""
    import xml.etree.ElementTree as ET
    url = f'https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(url, headers=HEADERS)
    data = urllib.request.urlopen(req, timeout=10).read()
    root = ET.fromstring(data)
    items = root.findall('.//item')[:5]
    articles = []
    for item in items:
        title = item.find('title')
        link = item.find('link')
        articles.append({
            'title': title.text if title is not None else '',
            'link': link.text.strip() if link is not None else '#',
            'source': '구글 뉴스'
        })
    return articles

def main():
    categories = {}

    # 1. IT/과학 (네이버 섹션 105)
    try:
        articles = scrape_section(105)
        if not articles:
            articles = scrape_google_news('IT 기술')
        categories['IT'] = articles
        print(f'IT: {len(articles)}개')
    except Exception as e:
        print(f'IT 스크래핑 실패: {e}', file=sys.stderr)
        try:
            categories['IT'] = scrape_google_news('IT 기술')
        except:
            categories['IT'] = []

    # 2. 반도체 (네이버 검색)
    try:
        articles = scrape_search('반도체')
        if not articles:
            articles = scrape_google_news('반도체')
        categories['반도체'] = articles
        print(f'반도체: {len(articles)}개')
    except Exception as e:
        print(f'반도체 스크래핑 실패: {e}', file=sys.stderr)
        try:
            categories['반도체'] = scrape_google_news('반도체')
        except:
            categories['반도체'] = []

    # 3. AI (네이버 검색)
    try:
        articles = scrape_search('AI 인공지능')
        if not articles:
            articles = scrape_google_news('AI 인공지능')
        categories['AI'] = articles
        print(f'AI: {len(articles)}개')
    except Exception as e:
        print(f'AI 스크래핑 실패: {e}', file=sys.stderr)
        try:
            categories['AI'] = scrape_google_news('AI 인공지능')
        except:
            categories['AI'] = []

    # 4. 사회 (네이버 섹션 102 = 사회)
    try:
        articles = scrape_section(102)
        if not articles:
            articles = scrape_google_news('사회')
        categories['사회'] = articles
        print(f'사회: {len(articles)}개')
    except Exception as e:
        print(f'사회 스크래핑 실패: {e}', file=sys.stderr)
        try:
            categories['사회'] = scrape_google_news('사회 뉴스')
        except:
            categories['사회'] = []

    output = {
        'categories': categories,
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    out_path = os.path.join(os.path.dirname(__file__), '..', 'news.json')
    out_path = os.path.normpath(out_path)
    # GitHub Actions용 경로
    if not os.path.exists(out_path):
        out_path = 'news.json'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in categories.values())
    print(f'\n총 {total}개 뉴스 저장 → {out_path}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
