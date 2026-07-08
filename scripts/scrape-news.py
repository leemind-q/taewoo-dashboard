#!/usr/bin/env python3
"""
네이버 뉴스 스크래퍼 v2 — 제목-링크 매칭 버그 수정
GitHub Actions에서 실행 → news.json 생성 → 자동 커밋
의존성: 없음 (표준 라이브러리만 사용)
"""
import urllib.request, urllib.parse, re, json, sys, os
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='replace')

def clean_text(text):
    text = text.strip()
    text = text.replace('&#x27;', "'").replace('&quot;', '"').replace('&amp;', '&')
    text = text.replace('&#39;', "'").replace('&lt;', '<').replace('&gt;', '>')
    return text

def is_valid_article_url(url):
    """기사 본문 URL만 허용, comment/talk/series 페이지 제외"""
    invalid_patterns = ['/comment/', '/talk/', '/series/', '/press/', '/reporter/']
    return all(p not in url for p in invalid_patterns)

def scrape_section(section_id):
    """네이버 뉴스 섹션 페이지 스크래핑 (section_id: 105=IT/과학, 102=사회 등)"""
    url = f'https://news.naver.com/section/{section_id}'
    html = fetch_html(url)

    # sa_item 컨테이너 내부에서 기사 링크+제목을 쌍으로 추출
    # 핵심: <a href="기사URL"> 안에 <strong>제목</strong>이 함께 있는 구조를 매칭
    pattern = r'<a\s[^>]*href="(https://n\.news\.naver\.com/mnews/article/\d+/\d+)"[^>]*>.*?<strong[^>]*class="[^"]*sa_text_strong[^"]*"[^>]*>([^<]+)</strong>'
    matches = re.findall(pattern, html, re.DOTALL)

    # comment 링크 필터
    matches = [(l, t) for l, t in matches if is_valid_article_url(l)]

    if not matches:
        # 폴백: 더 넓은 패턴 — 같은 <a> 태그 내에 strong 제목이 있는 경우
        pattern2 = r'href="(https://n\.news\.naver\.com/mnews/article/\d+/\d+)"[^>]*>.*?<strong[^>]*>([^<]+)</strong>'
        matches = re.findall(pattern2, html, re.DOTALL)
        matches = [(l, t) for l, t in matches if is_valid_article_url(l)]

    # 중복 제거 (URL 기준)
    seen = set()
    articles = []
    for link, title in matches:
        # URL 정규화 (쿼리 파라미터 제거)
        normalized = link.split('?')[0].split('#')[0]
        if normalized not in seen:
            seen.add(normalized)
            articles.append({'title': clean_text(title), 'link': link, 'source': '네이버 뉴스'})

    return articles[:5]

def scrape_search(query):
    """네이버 뉴스 검색 결과 스크래핑 — 제목-링크를 단일 정규식으로 쌍 추출"""
    url = f'https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(query)}&sort=1&nso=so:dd,p:all&sm=tab_opt'
    html = fetch_html(url)

    # 패턴1: news_tit 클래스의 <a> 태그 (제목이 텍스트 노드로 직접 들어있는 구조)
    pattern = r'<a[^>]*class="[^"]*news_tit[^"]*"[^>]*href="(https://n\.news\.naver\.com/mnews/article/\d+/\d+)[^"]*"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    matches = [(l, t) for l, t in matches if is_valid_article_url(l)]

    if not matches:
        # 패턴2: 일반 기사 링크 + 제목 텍스트
        pattern2 = r'href="(https://n\.news\.naver\.com/mnews/article/\d+/\d+[^"]*)"[^>]*>\s*([^<]+(?:</[^>]+>[^<]*)*)'
        matches = re.findall(pattern2, html, re.DOTALL)
        # HTML 태그 제거 후 정리
        cleaned = []
        for link, raw_title in matches:
            if is_valid_article_url(link):
                title = re.sub(r'<[^>]+>', '', raw_title).strip()
                if len(title) > 10:  # 의미 있는 제목만
                    cleaned.append((link, title))
        matches = cleaned

    seen = set()
    articles = []
    for link, title in matches:
        normalized = link.split('?')[0].split('#')[0]
        if normalized not in seen:
            seen.add(normalized)
            articles.append({'title': clean_text(title), 'link': link, 'source': '네이버 뉴스'})

    return articles[:5]

def scrape_google_news_rss(query):
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
        if title is not None and link is not None:
            articles.append({
                'title': title.text.strip() if title.text else '',
                'link': link.text.strip() if link.text else '#',
                'source': '구글 뉴스'
            })
    return articles

def fetch_category(name, fetcher_fn, fallback_query):
    """카테고리별 뉴스 수집 — fetcher 실패 시 Google RSS 폴백"""
    try:
        articles = fetcher_fn()
        if len(articles) >= 3:
            print(f'{name}: {len(articles)}개')
            return articles
        print(f'{name}: 스크래핑 {len(articles)}개 → RSS 폴백')
    except Exception as e:
        print(f'{name} 스크래핑 실패: {e}', file=sys.stderr)

    try:
        articles = scrape_google_news_rss(fallback_query)
        print(f'{name} (RSS): {len(articles)}개')
        return articles
    except Exception as e:
        print(f'{name} RSS 실패: {e}', file=sys.stderr)
        return []

def main():
    categories = {}

    categories['IT'] = fetch_category('IT',
        lambda: scrape_section(105), 'IT 기술 뉴스')

    categories['반도체'] = fetch_category('반도체',
        lambda: scrape_search('반도체'), '반도체 뉴스')

    categories['AI'] = fetch_category('AI',
        lambda: scrape_search('AI 인공지능'), 'AI 인공지능 뉴스')

    categories['사회'] = fetch_category('사회',
        lambda: scrape_section(102), '사회 뉴스')

    output = {
        'categories': categories,
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    out_path = os.path.join(os.path.dirname(__file__), '..', 'news.json')
    out_path = os.path.normpath(out_path)
    if not os.path.exists(out_path):
        out_path = 'news.json'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in categories.values())
    print(f'\n총 {total}개 뉴스 저장 → {out_path}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
