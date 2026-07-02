#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간다GO — 부산·경남 출장마사지 지역 안내 사이트 정적 생성기
- 모든 페이지: 프리미엄 팔레트 CSS / 오렌지 텔레그램 문의 버튼 푸터 / ≤80자 메타 디스크립션
  / JSON-LD 스키마(Organization·WebPage·BreadcrumbList·Service+Offer·FAQPage)
  / 가격표(60·90·120분) / 내부링크(롱테일 앵커) 노출
사용법: python3 build.py  →  루트에 정적 HTML 생성
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ 공통 설정
SITE_NAME = "간다GO"
SITE_TAGLINE = "부산·경남 출장마사지 지역 안내"
BASE_URL = "https://ganda-go.com"           # 배포 도메인(교체 지점)
PHONE = "0508-202-4719"                       # 전화예약
TEL_HREF = "tel:0508-202-4719"
# ── 텔레그램 링크(교체 지점: 실제 아이디로 이 한 줄만 수정) ──
TELEGRAM_BUILD = "https://t.me/gandago"       # 웹사이트 제작문의
TELEGRAM_PARTNER = "https://t.me/gandago"     # 제휴문의

# 가격표 (모든 지역/페이지 노출) — 실제 요금(Offer 스키마와 일치)
PRICING = [
    {"plan": "60분 코스", "amount": "90,000", "dur": "60분",
     "desc": "기본 컨디션·릴랙스 케어", "featured": False, "price": "90000", "min": 60},
    {"plan": "90분 코스", "amount": "150,000", "dur": "90분",
     "desc": "아로마 포함 추천 구성", "featured": True, "price": "150000", "min": 90},
    {"plan": "120분 코스", "amount": "180,000", "dur": "120분",
     "desc": "전신 집중 프리미엄 케어", "featured": False, "price": "180000", "min": 120},
]

# 권위 있는 외부 참고 링크(E-E-A-T / 정보 이득)
AUTH_LINKS = {
    "humetro": ("부산교통공사 도시철도 노선·역 정보", "https://www.humetro.busan.kr"),
    "korail": ("코레일 KTX 열차 시간·예매", "https://www.letskorail.com"),
    "busan": ("부산광역시 공식 누리집", "https://www.busan.go.kr"),
    "gyeongnam": ("경상남도 공식 누리집", "https://www.gyeongnam.go.kr"),
    "airport": ("한국공항공사 김해공항 안내", "https://www.airport.co.kr/gimhae"),
    "pipc": ("개인정보보호위원회", "https://www.pipc.go.kr"),
}

NAV = [
    ("부산·경남 홈", "/"),
    ("부산 생활권", "/busan/"),
    ("부산 구·군", "/busan/#gu"),
    ("경남 권역", "/gyeongnam/"),
    ("경남 시·군", "/gyeongnam/#si"),
    ("이용 장소", "/use/"),
    ("예약 전 확인", "/check/"),
    ("운영 기준", "/about/"),
    ("문의하기", "/contact/"),
]

PAGES = []  # (url_path, priority) 수집 → sitemap


def esc(s):
    return html.escape(str(s), quote=True)


def check_desc(desc):
    """메타 디스크립션 80자 이내 강제."""
    d = desc.strip()
    if len(d) > 80:
        raise ValueError(f"[80자 초과 {len(d)}자] {d}")
    return d


# ------------------------------------------------------------------ 스키마
def org_schema():
    return {
        "@type": "Organization",
        "@id": f"{BASE_URL}/#org",
        "name": SITE_NAME,
        "url": BASE_URL + "/",
        "telephone": PHONE,
        "description": "부산·경남 출장마사지·홈타이 생활권별 방문 가능 지역과 이용 기준을 안내하는 정보 사이트.",
        "areaServed": [{"@type": "AdministrativeArea", "name": n}
                       for n in ["부산광역시", "경상남도"]],
        "sameAs": [TELEGRAM_BUILD],
    }


def service_schema(area_name):
    """Service + Offer(실제 가격). 리뷰/평점 미포함."""
    offers = [{
        "@type": "Offer",
        "name": p["plan"],
        "price": p["price"],
        "priceCurrency": "KRW",
        "description": p["desc"],
        "availability": "https://schema.org/InStock",
    } for p in PRICING]
    return {
        "@type": "Service",
        "serviceType": "출장마사지·홈타이 방문 케어",
        "provider": {"@id": f"{BASE_URL}/#org"},
        "areaServed": {"@type": "Place", "name": area_name},
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "KRW",
            "lowPrice": "90000",
            "highPrice": "180000",
            "offerCount": len(PRICING),
            "offers": offers,
        },
    }


def webpage_schema(url, title, desc):
    return {
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": title,
        "description": desc,
        "isPartOf": {"@id": f"{BASE_URL}/#website"},
        "inLanguage": "ko-KR",
        "publisher": {"@id": f"{BASE_URL}/#org"},
    }


def website_schema():
    return {
        "@type": "WebSite",
        "@id": f"{BASE_URL}/#website",
        "url": BASE_URL + "/",
        "name": f"{SITE_NAME} · {SITE_TAGLINE}",
        "inLanguage": "ko-KR",
        "publisher": {"@id": f"{BASE_URL}/#org"},
    }


def breadcrumb_schema(crumbs):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [{
            "@type": "ListItem",
            "position": i + 1,
            "name": name,
            "item": BASE_URL + path if path else None,
        } for i, (name, path) in enumerate(crumbs)],
    }


def faq_schema(faqs):
    return {
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        } for q, a in faqs],
    }


def jsonld(*objs):
    graph = {"@context": "https://schema.org", "@graph": list(objs)}
    return ('<script type="application/ld+json">'
            + json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
            + "</script>")


# ------------------------------------------------------------------ HTML 조각
def header_html():
    links = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for label, href in NAV)
    return f"""<header class="site-header">
  <div class="container">
    <a class="brand" href="/"><span class="dot">G</span>{esc(SITE_NAME)}</a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav" aria-label="메뉴 열기">☰</button>
    <nav class="nav" id="nav" aria-label="주 메뉴">{links}</nav>
  </div>
</header>"""


def breadcrumb_html(crumbs):
    items = ""
    for name, path in crumbs:
        if path:
            items += f'<li><a href="{esc(path)}">{esc(name)}</a></li>'
        else:
            items += f'<li aria-current="page">{esc(name)}</li>'
    return f'<div class="crumbs"><div class="container"><ol>{items}</ol></div></div>'


def pricing_html(area_label="부산·경남 전 지역"):
    cards = ""
    for p in PRICING:
        badge = '<span class="price-badge">추천</span>' if p["featured"] else ""
        cls = "price-card featured" if p["featured"] else "price-card"
        btn = "btn btn-primary btn-block" if p["featured"] else "btn btn-ghost btn-block"
        cards += f"""<div class="{cls}">{badge}
      <div class="plan">{esc(p['plan'])}</div>
      <div class="amount">{esc(p['amount'])}<span class="won">원</span></div>
      <div class="dur">{esc(p['dur'])}</div>
      <div class="desc">{esc(p['desc'])}</div>
      <a class="{btn}" href="{esc(TELEGRAM_BUILD)}" target="_blank" rel="noopener">예약 문의</a>
    </div>"""
    return f"""<section class="section pricing" id="pricing" aria-labelledby="pricing-h">
  <div class="container">
    <div class="center" style="margin-bottom:1.6rem">
      <span class="eyebrow">요금 안내</span>
      <h2 id="pricing-h">이용 코스와 요금 살펴보기</h2>
      <p class="lead center" style="margin-inline:auto">60·90·120분 코스별 기준 요금이며, 추가 비용 없이 있는 그대로 안내해 드립니다. <span class="muted">({esc(area_label)} 동일 기준)</span></p>
    </div>
    <div class="price-grid">{cards}</div>
    <p class="price-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. <a href="/check/travel-fee/"><strong>상세 요금 안내 보기 →</strong></a></p>
  </div>
</section>"""


FOOTER_COLS = [
    ("부산", [
        ("해운대·센텀 생활권 안내", "/busan/area/haeundae-centum/"),
        ("서면·전포 생활권 안내", "/busan/area/seomyeon-jeonpo/"),
        ("광안리·수영 생활권 안내", "/busan/area/gwangalli-suyeong/"),
        ("부산 16개 구·군 전체 보기", "/busan/#gu"),
    ]),
    ("경남", [
        ("창원·김해·양산권 안내", "/gyeongnam/area/changwon-gimhae-yangsan/"),
        ("진주·사천권 안내", "/gyeongnam/area/jinju-sacheon/"),
        ("거제·통영·고성권 안내", "/gyeongnam/area/geoje-tongyeong-goseong/"),
        ("경남 시·군 전체 보기", "/gyeongnam/#si"),
    ]),
    ("예약 전 확인", [
        ("호텔·숙소 이용 전 확인", "/check/hotel-policy/"),
        ("오피스텔 관리 규정 확인", "/check/officetel-rule/"),
        ("추가 이동비 기준 확인", "/check/travel-fee/"),
        ("불법·선정적 서비스 불가 안내", "/check/service-policy/"),
    ]),
]


def footer_html():
    cols = ""
    for title, links in FOOTER_COLS:
        lis = "".join(f'<li><a href="{esc(h)}">{esc(t)}</a></li>' for t, h in links)
        cols += f"<div><h4>{esc(title)}</h4><ul>{lis}</ul></div>"
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-cta">
      <span class="eyebrow">문의하기</span>
      <h2>웹사이트 제작·제휴가 필요하신가요?</h2>
      <p class="muted">텔레그램으로 편하게 문의하시면 빠르게 안내해 드립니다.</p>
      <div class="cta-row">
        <a class="btn btn-primary btn-lg" href="{esc(TELEGRAM_BUILD)}" target="_blank" rel="noopener">✈ 웹사이트 제작문의</a>
        <a class="btn btn-primary btn-lg" href="{esc(TELEGRAM_PARTNER)}" target="_blank" rel="noopener">✈ 제휴문의</a>
      </div>
    </div>

    <div class="footer-grid">
      <div class="biz">
        <div class="biz-name">{esc(SITE_NAME)}</div>
        <p class="muted" style="margin:.4rem 0">{esc(SITE_TAGLINE)} · 생활권별 방문 가능 지역 안내</p>
        <p>전화예약 <a class="tel" href="{esc(TEL_HREF)}">{esc(PHONE)}</a></p>
        <p class="cta-row" style="gap:.5rem;margin-top:.6rem">
          <a class="btn btn-primary" href="{esc(TELEGRAM_BUILD)}" target="_blank" rel="noopener">✈ 제작문의</a>
          <a class="btn btn-primary" href="{esc(TELEGRAM_PARTNER)}" target="_blank" rel="noopener">✈ 제휴문의</a>
        </p>
      </div>
      {cols}
    </div>

    <div class="footer-bottom">
      <span>© 2026 {esc(SITE_NAME)}. 부산·경남 출장마사지 지역 안내.</span>
      <span class="policy-links">
        <a href="/check/privacy/">개인정보 처리 기준</a>
        <a href="/check/service-policy/">불법·선정적 서비스 불가 안내</a>
        <a href="/check/customer-notice/">고객 유의사항</a>
      </span>
    </div>
  </div>
</footer>"""


# ------------------------------------------------------------------ 페이지 조립
def page(url, title, desc, crumbs, body_html, faqs=None,
         area_name="부산·경남", show_pricing=True, priority=0.6, index=True):
    desc = check_desc(desc)
    full_url = BASE_URL + url
    schemas = [website_schema(), org_schema(),
               webpage_schema(full_url, title, desc),
               breadcrumb_schema(crumbs),
               service_schema(area_name)]
    if faqs:
        schemas.append(faq_schema(faqs))
    robots = "index,follow" if index else "noindex,follow"
    og_img = f"{BASE_URL}/assets/og-default.png"
    pricing_block = pricing_html(area_name) if show_pricing else ""
    doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{esc(full_url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(full_url)}">
<meta property="og:image" content="{esc(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0B1120">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
{jsonld(*schemas)}
</head>
<body>
<a class="skip" href="#main">본문 바로가기</a>
{header_html()}
{breadcrumb_html(crumbs)}
<main id="main">
{body_html}
{pricing_block}
</main>
{footer_html()}
<script src="/assets/js/site.js" defer></script>
</body>
</html>"""
    out_dir = os.path.join(ROOT, url.strip("/"))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    PAGES.append((url, priority if index else 0.0, index))


# ------------------------------------------------------------------ 본문 조각 헬퍼
def sec(title, inner, cls="section", hid=None, lead=None):
    h = f' id="{hid}"' if hid else ""
    leadhtml = f'<p class="lead">{lead}</p>' if lead else ""
    return f'<section class="{cls}"{h}><div class="container"><h2>{esc(title)}</h2>{leadhtml}{inner}</div></section>'


def card_grid(items, cols=3):
    cards = ""
    for it in items:
        title = it[0]; meta = it[1]; href = it[2]
        cards += (f'<a class="card" href="{esc(href)}"><h3>{esc(title)}</h3>'
                  f'<p class="card-meta">{esc(meta)}</p>'
                  f'<p class="arrow">자세히 보기 →</p></a>')
    return f'<div class="grid cols-{cols}">{cards}</div>'


def taglist(items):
    a = "".join(f'<a href="{esc(h)}">{esc(t)}</a>' for t, h in items)
    return f'<div class="taglist">{a}</div>'


def checklist(items):
    lis = "".join(f"<li>{esc(x)}</li>" for x in items)
    return f'<ul class="checklist">{lis}</ul>'


def faq_block(faqs):
    ds = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faqs)
    return f'<div class="faq">{ds}</div>'


def whw_block(who, how, why):
    return (f'<div class="whw">'
            f'<div class="card"><h3>Who · 누가</h3><p class="muted">{esc(who)}</p></div>'
            f'<div class="card"><h3>How · 어떻게</h3><p class="muted">{esc(how)}</p></div>'
            f'<div class="card"><h3>Why · 왜</h3><p class="muted">{esc(why)}</p></div></div>')


def auth_note(keys):
    lis = "".join(f'<li><a href="{esc(AUTH_LINKS[k][1])}" target="_blank" rel="noopener nofollow">{esc(AUTH_LINKS[k][0])}</a></li>'
                  for k in keys)
    return (f'<div class="callout"><strong>참고 자료</strong> — 이동·교통 정보는 공식 기관 자료로 직접 확인하실 수 있습니다.'
            f'<ul>{lis}</ul></div>')


# 공통 예약 전 체크리스트(모든 지역 페이지 삽입)
COMMON_CHECK = [
    "방문 주소를 정확히 확인했나요? (부산/경남, 세부 생활권)",
    "가까운 역·터미널·주요 도로를 확인했나요?",
    "호텔·숙소 이용 가능 여부와 프런트 확인 방식을 확인했나요?",
    "오피스텔 공동현관·엘리베이터·관리 규정을 확인했나요?",
    "외곽 지역 추가 이동 기준을 확인했나요?",
    "예약 가능 시간과 변경 기준을 확인했나요?",
    "개인정보 처리 기준과 불법·선정적 서비스 불가 안내를 확인했나요?",
]

COMMON_FAQ_TAIL = [
    ("불법·선정적 서비스도 가능한가요?", "불법·선정적 서비스는 제공하거나 안내하지 않습니다. 건전한 컨디션·릴랙스 케어만 안내합니다."),
    ("개인정보는 어떻게 처리하나요?", "예약 확인과 연락에 필요한 최소 정보만 확인하며, 자세한 내용은 개인정보 처리 기준 페이지에서 확인할 수 있습니다."),
    ("요금은 지역마다 다른가요?", "60·90·120분 코스 기준 요금은 동일하며, 지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다."),
]

USE_LINKS = [
    ("자택 이용 기준 확인하기", "/use/home/"),
    ("호텔·숙소 이용 기준 확인하기", "/use/hotel/"),
    ("오피스텔 이용 기준 확인하기", "/use/officetel/"),
    ("업무지구·산단 방문 기준 확인하기", "/use/business-district/"),
    ("KTX·터미널 인접 이용 기준 확인하기", "/use/station-terminal/"),
    ("야간 예약 기준 확인하기", "/use/night/"),
]
CHECK_LINKS = [
    ("방문 주소 확인 방법 보기", "/check/address/"),
    ("건물 출입 방식 확인하기", "/check/building-access/"),
    ("추가 이동비 기준 확인하기", "/check/travel-fee/"),
    ("예약 가능 시간 확인하기", "/check/time/"),
    ("개인정보 처리 기준 보기", "/check/privacy/"),
    ("불법·선정적 서비스 불가 안내", "/check/service-policy/"),
]


# ------------------------------------------------------------------ 데이터: 부산 생활권(8)
BUSAN_AREAS = [
  {"slug":"haeundae-centum","name":"해운대·센텀권","zones":"해운대·중동·우동·센텀시티·마린시티·송정",
   "kind":"호텔·숙소, 해안 관광지, 오피스텔, 센텀 업무지구 중심",
   "over":["해운대·센텀권은 부산에서 관광 숙소와 업무지구가 가장 밀집한 생활권입니다. 해운대해수욕장과 마린시티의 호텔·레지던스, 센텀시티의 오피스텔과 업무 빌딩이 가까이 붙어 있어 방문 목적이 관광·출장·거주로 다양하게 나뉩니다.",
          "같은 해운대구 안에서도 중동·우동의 호텔 밀집 구역, 센텀시티의 오피스텔·업무지구, 송정의 해안 주거지는 건물 출입 방식과 방문 가능 시간대가 서로 다릅니다. 따라서 시·구 이름보다 정확한 방문 주소와 숙소 형태를 먼저 확인하는 것이 안전합니다."],
   "stations":["장산역","해운대역","중동역","벡스코역","센텀시티역"],
   "near":[("서면·전포 생활권 안내","/busan/area/seomyeon-jeonpo/"),("광안리·수영 생활권 안내","/busan/area/gwangalli-suyeong/"),("해운대구 구·군 안내","/busan/haeundae-gu/")]},
  {"slug":"seomyeon-jeonpo","name":"서면·전포권","zones":"서면·전포·부전·범천",
   "kind":"부산 중심 상권, 숙소, 오피스텔, 환승역 중심",
   "over":["서면·전포권은 부산 도심 교통의 중심입니다. 1호선과 2호선이 만나는 서면역을 축으로 상권·숙소·오피스텔이 촘촘하게 이어져, 부산 어느 방향으로든 이동이 빠른 것이 특징입니다.",
          "전포 카페거리와 부전동 상권, 범천동 주거지가 가까워 방문 장소가 오피스텔인지 숙소인지에 따라 공동현관·엘리베이터 확인 사항이 달라집니다. 환승 인구가 많은 만큼 예약 가능 시간대를 미리 맞추는 것이 좋습니다."],
   "stations":["서면역","부전역","전포역","범내골역"],
   "near":[("해운대·센텀 생활권 안내","/busan/area/haeundae-centum/"),("동래·연산 생활권 안내","/busan/area/dongnae-yeonsan/"),("부산진구 구·군 안내","/busan/busanjin-gu/")]},
  {"slug":"gwangalli-suyeong","name":"광안리·수영권","zones":"광안리·수영·민락·남천",
   "kind":"숙소, 해안 상권, 주거지 혼합형",
   "over":["광안리·수영권은 해안 상권과 주거지가 섞인 생활권입니다. 광안리해수욕장 주변의 숙소·게스트하우스, 남천동의 주거 단지, 민락동의 회센터 상권이 가까워 방문 목적이 관광과 거주로 나뉩니다.",
          "광안대교 조망 숙소와 오피스텔이 많아 건물 출입 방식이 제각각입니다. 프런트 확인이 필요한 숙소인지, 공동현관 비밀번호가 있는 오피스텔인지 예약 전에 확인하면 방문이 매끄럽습니다."],
   "stations":["광안역","수영역","금련산역","남천역"],
   "near":[("해운대·센텀 생활권 안내","/busan/area/haeundae-centum/"),("서면·전포 생활권 안내","/busan/area/seomyeon-jeonpo/"),("수영구 구·군 안내","/busan/suyeong-gu/")]},
  {"slug":"busan-station-nampo","name":"부산역·남포권","zones":"부산역·초량·남포·자갈치·중앙동",
   "kind":"KTX, 출장객, 관광 숙소, 도심 이동 중심",
   "over":["부산역·남포권은 KTX 부산역을 중심으로 한 관문 생활권입니다. 초량 차이나타운, 중앙동 업무지구, 남포동·자갈치 관광 상권이 이어져 출장객과 관광객의 숙소 이용이 많습니다.",
          "KTX로 도착해 인근 호텔에 머무는 출장 방문이 잦은 지역이라, 도착 시간과 예약 가능 시간을 맞추는 것이 중요합니다. 남포동은 관광 숙소, 중앙동은 업무용 오피스텔이 많아 방문 장소별 확인 사항이 다릅니다."],
   "stations":["부산역","중앙역","남포역","자갈치역","초량역"],
   "near":[("동래·연산 생활권 안내","/busan/area/dongnae-yeonsan/"),("서면·전포 생활권 안내","/busan/area/seomyeon-jeonpo/"),("중구 구·군 안내","/busan/jung-gu/")]},
  {"slug":"dongnae-yeonsan","name":"동래·연산권","zones":"동래·온천장·연산·교대",
   "kind":"주거지, 상권, 지하철 환승 중심",
   "over":["동래·연산권은 주거지와 행정·상업 기능이 함께 있는 생활권입니다. 동래·온천장의 오래된 주거·상권, 연산동 교차로의 업무지구, 교대 주변의 학원가가 이어져 거주 인구 방문 비중이 높습니다.",
          "1호선과 3호선이 만나는 연산역, 1호선과 4호선이 만나는 동래역이 있어 환승 이동이 편리합니다. 오피스텔과 아파트가 섞여 있어 공동현관·관리 규정 확인이 필요합니다."],
   "stations":["동래역","연산역","교대역","온천장역","명륜역"],
   "near":[("서면·전포 생활권 안내","/busan/area/seomyeon-jeonpo/"),("부산역·남포 생활권 안내","/busan/area/busan-station-nampo/"),("동래구 구·군 안내","/busan/dongnae-gu/")]},
  {"slug":"sasang-hadan","name":"사상·하단권","zones":"사상·괘법·주례·하단·당리",
   "kind":"서부산 교통, 터미널, 산업권, 주거지 중심",
   "over":["사상·하단권은 서부산 교통과 산업의 축입니다. 사상 서부시외버스터미널과 사상역, 하단역을 중심으로 산업단지·주거지가 이어져 출퇴근·출장 이동이 많습니다.",
          "사상은 터미널과 산업권, 하단·당리는 주거 밀집 지역이라 방문 장소가 오피스텔인지 아파트인지 사전 확인이 필요합니다. 서부산 외곽으로 이어지는 지역은 이동 거리에 따른 기준을 함께 확인하는 것이 좋습니다."],
   "stations":["사상역","하단역","괘법르네시떼역","동매역","신평역"],
   "near":[("명지·강서 생활권 안내","/busan/area/myeongji-gangseo/"),("서면·전포 생활권 안내","/busan/area/seomyeon-jeonpo/"),("사상구 구·군 안내","/busan/sasang-gu/")]},
  {"slug":"myeongji-gangseo","name":"명지·강서권","zones":"명지·녹산·신호·김해공항 인접권",
   "kind":"신도시, 산업단지, 공항 인접권 중심",
   "over":["명지·강서권은 신도시와 산업단지, 김해공항이 함께 있는 서부산 생활권입니다. 명지국제신도시의 신축 오피스텔·아파트, 녹산·신호 산업단지, 공항 인접 숙소가 이어져 이동 목적이 다양합니다.",
          "신도시 오피스텔은 공동현관과 관리 규정이 엄격한 편이라 방문 전 출입 방식을 확인해야 합니다. 김해공항 인접권은 항공 이용객의 숙소 방문이 있어 도착·예약 시간 조율이 중요합니다."],
   "stations":["김해공항역","공항역","대저역","서부산유통지구역"],
   "near":[("사상·하단 생활권 안내","/busan/area/sasang-hadan/"),("강서구 구·군 안내","/busan/gangseo-gu/"),("창원·김해·양산권 안내","/gyeongnam/area/changwon-gimhae-yangsan/")]},
  {"slug":"gijang-jeonggwan","name":"기장·정관권","zones":"기장·정관·일광·오시리아",
   "kind":"외곽 이동 기준, 숙소, 관광지, 주거지 중심",
   "over":["기장·정관권은 부산 동북부 외곽 생활권입니다. 정관신도시의 주거 단지, 일광·기장의 해안 관광지, 오시리아 관광단지의 리조트·숙소가 넓게 흩어져 있어 이동 거리 확인이 특히 중요합니다.",
          "도심에서 다소 떨어져 있어 방문 가능 여부와 추가 이동 기준을 예약 전에 확인하는 것이 좋습니다. 오시리아 리조트·숙소는 프런트 확인 방식이, 정관신도시는 오피스텔·아파트 관리 규정이 방문에 영향을 줍니다."],
   "stations":["오시리아역","기장역","일광역","좌천역"],
   "near":[("해운대·센텀 생활권 안내","/busan/area/haeundae-centum/"),("기장군 구·군 안내","/busan/gijang-gun/"),("동래·연산 생활권 안내","/busan/area/dongnae-yeonsan/")]},
]


# ------------------------------------------------------------------ 데이터: 부산 16개 구·군
BUSAN_GU = [
  {"slug":"jung-gu","name":"중구","h":"남포·중앙·자갈치","area":"busan-station-nampo","stations":["남포역","자갈치역","중앙역"]},
  {"slug":"seo-gu","name":"서구","h":"송도·충무·동대신","area":"busan-station-nampo","stations":["자갈치역","토성역","동대신역"]},
  {"slug":"dong-gu","name":"동구","h":"부산역·초량·범일","area":"busan-station-nampo","stations":["부산역","초량역","범일역"]},
  {"slug":"yeongdo-gu","name":"영도구","h":"영도·태종대·남항","area":"busan-station-nampo","stations":["남포역"]},
  {"slug":"busanjin-gu","name":"부산진구","h":"서면·전포·부전","area":"seomyeon-jeonpo","stations":["서면역","부전역","전포역"]},
  {"slug":"dongnae-gu","name":"동래구","h":"동래·온천장·사직","area":"dongnae-yeonsan","stations":["동래역","온천장역","사직역"]},
  {"slug":"nam-gu","name":"남구","h":"대연·경성대·문현","area":"gwangalli-suyeong","stations":["경성대부경대역","대연역","문현역"]},
  {"slug":"buk-gu","name":"북구","h":"화명·덕천·구포","area":"sasang-hadan","stations":["화명역","덕천역","구포역"]},
  {"slug":"haeundae-gu","name":"해운대구","h":"해운대·센텀·마린시티·송정","area":"haeundae-centum","stations":["해운대역","센텀시티역","장산역"]},
  {"slug":"saha-gu","name":"사하구","h":"하단·다대포·괴정","area":"sasang-hadan","stations":["하단역","다대포해수욕장역","괴정역"]},
  {"slug":"geumjeong-gu","name":"금정구","h":"부산대·장전·구서","area":"dongnae-yeonsan","stations":["부산대역","장전역","구서역"]},
  {"slug":"gangseo-gu","name":"강서구","h":"명지·녹산·김해공항 인접권","area":"myeongji-gangseo","stations":["김해공항역","대저역"]},
  {"slug":"yeonje-gu","name":"연제구","h":"연산·교대·시청","area":"dongnae-yeonsan","stations":["연산역","교대역","시청역"]},
  {"slug":"suyeong-gu","name":"수영구","h":"광안리·수영·민락","area":"gwangalli-suyeong","stations":["광안역","수영역","민락역"]},
  {"slug":"sasang-gu","name":"사상구","h":"사상·괘법·주례","area":"sasang-hadan","stations":["사상역","괘법르네시떼역","주례역"]},
  {"slug":"gijang-gun","name":"기장군","h":"기장·정관·일광·오시리아","area":"gijang-jeonggwan","stations":["기장역","오시리아역","일광역"]},
]

# ------------------------------------------------------------------ 데이터: 경남 권역(5)
GN_AREAS = [
  {"slug":"changwon-gimhae-yangsan","name":"창원·김해·양산권","zones":"창원·김해·양산·밀양 일부",
   "kind":"산업단지, 업무지구, 신도시, KTX·고속도로 이동 기준",
   "over":["창원·김해·양산권은 경남에서 인구와 산업이 가장 집중된 권역입니다. 창원국가산단과 업무지구, 김해 장유·율하 신도시, 양산 물금신도시가 이어져 출퇴근·출장 이동 수요가 큽니다.",
          "도시 간 이동 거리가 짧지 않아 어느 생활권인지 먼저 확인하는 것이 중요합니다. 산업단지 인접 오피스텔, 신도시 아파트, 업무지구 숙소는 각각 출입 방식과 방문 가능 시간이 다릅니다."],
   "cities":[("창원시","/gyeongnam/changwon-si/"),("김해시","/gyeongnam/gimhae-si/"),("양산시","/gyeongnam/yangsan-si/")],
   "auth":["gyeongnam","korail"]},
  {"slug":"jinju-sacheon","name":"진주·사천권","zones":"진주·사천·산청 일부",
   "kind":"혁신도시, 대학가, 항공산업, 출장 숙소 중심",
   "over":["진주·사천권은 서부 경남의 중심 권역입니다. 진주혁신도시의 공공기관과 대학가, 사천의 항공산업단지가 있어 출장·거주 방문이 함께 나타납니다.",
          "진주는 혁신도시와 평거·가좌 주거지, 사천은 삼천포·항공단지로 생활권이 나뉩니다. KTX 진주역과 고속버스 이동이 많아 도착 시간에 맞춘 예약이 편리합니다."],
   "cities":[("진주시","/gyeongnam/jinju-si/"),("사천시","/gyeongnam/sacheon-si/")],
   "auth":["gyeongnam","korail"]},
  {"slug":"geoje-tongyeong-goseong","name":"거제·통영·고성권","zones":"거제·통영·고성",
   "kind":"조선업, 해안 관광, 숙소, 장거리 이동 기준",
   "over":["거제·통영·고성권은 남해안 조선업과 관광이 함께하는 권역입니다. 거제 고현·옥포의 조선소 배후 상권, 통영의 항구 관광지, 고성의 해안 지역이 넓게 퍼져 있습니다.",
          "도심에서 이동 거리가 길어 방문 가능 여부와 추가 이동 기준을 예약 전에 반드시 확인해야 합니다. 관광 숙소와 조선업 배후 오피스텔이 섞여 있어 방문 장소별 확인 사항이 다릅니다."],
   "cities":[("거제시","/gyeongnam/geoje-si/"),("통영시","/gyeongnam/tongyeong-si/")],
   "auth":["gyeongnam"]},
  {"slug":"miryang-changnyeong-haman","name":"밀양·창녕·함안권",
   "zones":"밀양·창녕·함안·의령","kind":"중소도시, 산업권, 외곽 방문 기준",
   "over":["밀양·창녕·함안권은 경남 내륙의 중소도시 권역입니다. 밀양 시가지와 KTX 밀양역, 창녕·함안·의령의 산업·농촌 지역이 넓게 분포합니다.",
          "생활권이 흩어져 있어 방문 가능 여부와 이동 기준 확인이 특히 중요합니다. 무리한 색인보다 실제 방문 수요가 있는 지역 위주로 안내합니다."],
   "cities":[("밀양시","/gyeongnam/miryang-si/")],
   "auth":["gyeongnam","korail"]},
  {"slug":"namhae-hadong-west","name":"남해·하동·서북부권",
   "zones":"남해·하동·함양·거창·합천·산청","kind":"관광지, 펜션, 리조트, 장거리 이동 가능 여부 확인 중심",
   "over":["남해·하동·서북부권은 관광지와 펜션·리조트가 중심인 권역입니다. 남해·하동의 해안·강변 관광지, 함양·거창·합천·산청의 산간 리조트가 넓게 분포합니다.",
          "장거리 이동 지역이 많아 방문 가능 여부를 먼저 확인해야 합니다. 펜션·리조트 이용 시 프런트 확인 방식과 객실 출입 방법을 미리 확인하는 것이 좋습니다."],
   "cities":[],
   "auth":["gyeongnam"]},
]

# ------------------------------------------------------------------ 데이터: 경남 핵심 시(8, 1차 색인)
GN_CITIES = [
  {"slug":"changwon-si","name":"창원시","h":"상남·중앙·마산·진해","area":"changwon-gimhae-yangsan","areaName":"창원·김해·양산권",
   "life":"창원 상남·중앙, 마산 합포·회원, 진해 석동·용원",
   "over":["창원시는 옛 창원·마산·진해가 통합된 경남 최대 도시입니다. 상남·중앙동 업무·상업지구, 마산 합포·회원의 원도심 상권, 진해의 해군·조선 배후 지역까지 생활권이 넓게 나뉩니다.",
          "창원국가산단과 업무지구 인근의 오피스텔, 신도시 아파트, 상권 숙소가 섞여 있어 방문 장소를 먼저 확인해야 합니다. 마산·진해까지 이동 거리가 있어 어느 생활권인지 확인하는 것이 중요합니다."],
   "stations":["창원중앙역","창원역","마산역"],"auth":["korail","gyeongnam"]},
  {"slug":"gimhae-si","name":"김해시","h":"장유·율하·내외·삼계","area":"changwon-gimhae-yangsan","areaName":"창원·김해·양산권",
   "life":"장유·율하, 내외·삼계, 김해공항 인접권",
   "over":["김해시는 부산·창원과 맞닿은 성장 도시입니다. 장유·율하 신도시, 내외·삼계 주거지, 김해공항 인접권이 이어져 부산 서부와 생활권이 가깝습니다.",
          "신도시 오피스텔과 아파트가 많아 공동현관·관리 규정 확인이 중요합니다. 김해공항과 가까워 항공 이용객의 숙소 방문도 있어 도착·예약 시간 조율이 필요합니다."],
   "stations":["김해시청역","부원역","봉황역"],"auth":["airport","gyeongnam"]},
  {"slug":"yangsan-si","name":"양산시","h":"물금·증산·덕계·서창","area":"changwon-gimhae-yangsan","areaName":"창원·김해·양산권",
   "life":"물금·증산, 덕계·서창",
   "over":["양산시는 부산 도시철도 2호선이 연결되는 부산 생활권 연계 도시입니다. 물금신도시의 신축 단지, 증산·덕계·서창의 주거지가 이어져 부산·울산으로의 이동이 편리합니다.",
          "신도시 오피스텔·아파트가 많아 출입 방식과 방문 가능 시간을 확인해야 합니다. 부산 노포·울산 방향 이동이 있어 인접 지역 기준도 함께 확인하면 좋습니다."],
   "stations":["양산역","남양산역","증산역"],"auth":["korail","gyeongnam"]},
  {"slug":"jinju-si","name":"진주시","h":"혁신도시·평거·가좌","area":"jinju-sacheon","areaName":"진주·사천권",
   "life":"진주혁신도시, 평거·가좌",
   "over":["진주시는 서부 경남의 행정·교육 중심 도시입니다. 진주혁신도시의 공공기관, 평거·가좌 주거지, 경상국립대 대학가가 이어져 출장·거주 방문이 함께 나타납니다.",
          "혁신도시 오피스텔과 원도심 숙소가 섞여 있어 방문 장소별 확인 사항이 다릅니다. KTX 진주역과 시외버스 이동이 많아 도착 시간에 맞춘 예약이 편리합니다."],
   "stations":["진주역"],"auth":["korail","gyeongnam"]},
  {"slug":"geoje-si","name":"거제시","h":"고현·옥포·장평","area":"geoje-tongyeong-goseong","areaName":"거제·통영·고성권",
   "life":"고현·옥포, 장평",
   "over":["거제시는 조선업과 해안 관광이 함께하는 섬 도시입니다. 고현 도심 상권, 옥포·장평의 조선소 배후 지역, 해안 관광지가 넓게 분포합니다.",
          "도심에서 이동 거리가 길어 방문 가능 여부와 추가 이동 기준을 먼저 확인해야 합니다. 조선업 배후 오피스텔과 관광 숙소가 섞여 있어 방문 장소를 정확히 확인하는 것이 좋습니다."],
   "stations":["고현버스터미널"],"auth":["gyeongnam"]},
  {"slug":"tongyeong-si","name":"통영시","h":"무전·죽림·항남","area":"geoje-tongyeong-goseong","areaName":"거제·통영·고성권",
   "life":"무전·죽림, 항남",
   "over":["통영시는 남해안 대표 관광 도시입니다. 무전·죽림의 주거·상업지구, 항남동 항구 관광지가 이어져 관광 숙소 방문이 많습니다.",
          "관광 성수기에는 숙소 프런트 확인 방식과 객실 출입 방법을 미리 확인하는 것이 좋습니다. 도심과 외곽 관광지의 이동 거리가 달라 방문 가능 여부를 먼저 확인해야 합니다."],
   "stations":["통영종합버스터미널"],"auth":["gyeongnam"]},
  {"slug":"sacheon-si","name":"사천시","h":"사천읍·삼천포·항공단지","area":"jinju-sacheon","areaName":"진주·사천권",
   "life":"사천읍, 삼천포, 항공산업단지",
   "over":["사천시는 항공산업과 해안 관광이 함께하는 도시입니다. 사천읍 행정지구, 삼천포 항구 상권, 항공산업단지 배후 지역으로 생활권이 나뉩니다.",
          "항공단지 인근 오피스텔과 삼천포 관광 숙소가 섞여 있어 방문 장소를 확인해야 합니다. 진주와 가까워 인접 권역 이동 기준도 함께 확인하면 편리합니다."],
   "stations":["사천공항","사천시외버스터미널"],"auth":["airport","gyeongnam"]},
  {"slug":"miryang-si","name":"밀양시","h":"내이·삼문","area":"miryang-changnyeong-haman","areaName":"밀양·창녕·함안권",
   "life":"내이·삼문 시가지",
   "over":["밀양시는 경남 내륙 교통의 요지입니다. 내이·삼문동 시가지와 KTX 밀양역을 중심으로 생활권이 형성되어 있습니다.",
          "시가지 외곽으로는 농촌·산업 지역이 넓게 퍼져 있어 방문 가능 여부와 이동 기준을 먼저 확인해야 합니다. KTX 밀양역 이용객의 방문이 있어 도착 시간에 맞춘 예약이 편리합니다."],
   "stations":["밀양역"],"auth":["korail","gyeongnam"]},
]

# ------------------------------------------------------------------ 데이터: 경남 2차 색인 시·군(5, 실수요·고유 콘텐츠)
GN_CITIES_2 = [
  {"slug":"haman-gun","name":"함안군","h":"가야·칠원","area":"miryang-changnyeong-haman","areaName":"밀양·창녕·함안권",
   "life":"가야읍, 칠원·칠서",
   "over":["함안군은 창원·마산 생활권과 바로 맞닿은 경남 중부의 군입니다. 군청이 있는 가야읍 시가지와, 마산·창원으로 출퇴근이 잦은 칠원읍·칠서 산업단지 배후가 생활권의 축을 이룹니다.",
          "칠서산업단지 인근에는 근로자 대상 오피스텔·원룸이 형성되어 있어 방문 장소가 산단 배후 주거인지 읍 시가지인지에 따라 이동 기준이 다릅니다. 창원·마산과 가까워 인접 도시 생활권 기준을 함께 확인하면 방문 가능 여부를 판단하기 쉽습니다."],
   "stations":["함안역","함안시외버스터미널"],"auth":["gyeongnam"],"index":True},
  {"slug":"changnyeong-gun","name":"창녕군","h":"창녕·남지·부곡","area":"miryang-changnyeong-haman","areaName":"밀양·창녕·함안권",
   "life":"창녕읍, 남지읍, 부곡온천",
   "over":["창녕군은 낙동강과 우포늪을 낀 경남 내륙 북부의 군입니다. 창녕읍 행정 시가지, 낙동강변 남지읍 상권, 그리고 전국적으로 알려진 부곡온천 관광·숙박 지구로 생활권이 나뉩니다.",
          "특히 부곡온천 일대는 호텔·콘도·펜션 숙박 수요가 뚜렷해, 관광 숙소 방문 시 프런트 확인 방식과 객실 출입 방법을 미리 확인하는 것이 좋습니다. 시가지와 온천지구, 강변 지역의 이동 거리가 달라 방문 주소를 먼저 확인해야 합니다."],
   "stations":["창녕시외버스터미널","남지시외버스터미널"],"auth":["gyeongnam"],"index":True},
  {"slug":"goseong-gun","name":"고성군","h":"고성읍·당항포","area":"geoje-tongyeong-goseong","areaName":"거제·통영·고성권",
   "life":"고성읍, 당항포 관광지, 동해면 조선특구",
   "over":["고성군은 통영·거제와 이어지는 남해안 관광·조선 배후 지역입니다. 고성읍 시가지, 공룡엑스포로 알려진 당항포 관광지, 동해면 일대 조선산업특구가 넓게 흩어져 있습니다.",
          "관광지와 조선 배후 지역, 읍 시가지의 성격이 달라 방문 장소를 정확히 확인해야 합니다. 통영·거제 도심에서 이동하는 경우가 많아 인접 권역의 이동 기준을 함께 확인하면 방문 가능 여부를 판단하기 쉽습니다."],
   "stations":["고성시외버스터미널"],"auth":["gyeongnam"],"index":True},
  {"slug":"hadong-gun","name":"하동군","h":"하동읍·화개","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"하동읍, 화개·악양, 섬진강변",
   "over":["하동군은 섬진강과 지리산 자락이 만나는 서부 경남의 관광 군입니다. 하동읍 시가지, 화개장터·쌍계사로 이어지는 화개·악양 관광지, 섬진강변 펜션·리조트가 생활권을 이룹니다.",
          "관광·펜션 방문이 많아 성수기에는 숙소 프런트 확인 방식과 객실 출입 방법을 미리 확인하는 것이 좋습니다. 남해·구례와 이어지는 외곽 관광지는 이동 거리가 길어 방문 가능 여부를 먼저 확인해야 합니다."],
   "stations":["하동역","하동시외버스터미널"],"auth":["korail","gyeongnam"],"index":True},
  {"slug":"namhae-gun","name":"남해군","h":"남해읍·상주","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"남해읍, 상주·미조, 창선",
   "over":["남해군은 다리로 연결된 섬 전체가 관광지인 남해안의 군입니다. 남해읍 중심가, 독일마을·다랭이마을·상주은모래비치 등 해안 관광지, 창선-삼천포대교로 사천과 이어지는 창선면이 생활권을 이룹니다.",
          "펜션·리조트 숙박 수요가 커서 객실 출입 방법과 프런트 확인 방식을 예약 전에 확인하는 것이 좋습니다. 섬 특성상 관광지 간 이동 거리가 길어 방문 가능 여부와 이동 기준을 먼저 확인해야 합니다."],
   "stations":["남해시외버스터미널"],"auth":["gyeongnam"],"index":True},
]

# ------------------------------------------------------------------ 데이터: 경남 3차 시·군(5, 외곽 산간·noindex / 도어웨이 회피)
GN_CITIES_3 = [
  {"slug":"uiryeong-gun","name":"의령군","h":"의령읍","area":"miryang-changnyeong-haman","areaName":"밀양·창녕·함안권",
   "life":"의령읍 시가지",
   "over":["의령군은 남강과 정암(솥바위)으로 알려진 경남 내륙의 농촌 군입니다. 의령읍 시가지를 중심으로 생활권이 좁게 형성되어 있고, 나머지 지역은 농촌·산간으로 넓게 퍼져 있습니다.",
          "방문 수요가 크지 않고 이동 거리가 긴 지역이 많아, 방문 가능 여부를 먼저 확인해야 합니다. 현재는 색인보다 실제 문의 데이터를 확인한 뒤 안내하는 지역으로 관리합니다."],
   "stations":["의령시외버스터미널"],"auth":["gyeongnam"],"index":False},
  {"slug":"sancheong-gun","name":"산청군","h":"산청읍·동의보감촌","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"산청읍, 지리산 동의보감촌",
   "over":["산청군은 지리산 자락의 한방·산림 관광지로 알려진 서부 경남의 군입니다. 산청읍 시가지와 동의보감촌 한방테마 관광지, 지리산 산간 지역이 생활권을 이룹니다.",
          "산간 관광지가 넓게 흩어져 있어 이동 거리가 길고 방문 수요가 제한적입니다. 방문 가능 여부를 먼저 확인하는 지역으로 관리하며, 실제 수요가 확인되면 순차적으로 안내합니다."],
   "stations":["산청시외버스터미널"],"auth":["gyeongnam"],"index":False},
  {"slug":"hamyang-gun","name":"함양군","h":"함양읍·상림","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"함양읍, 상림숲",
   "over":["함양군은 지리산과 덕유산 사이에 자리한 서북부 경남의 산간 군입니다. 함양읍 시가지와 천년 숲 상림, 산간 관광지가 생활권을 이룹니다.",
          "도심에서 이동 거리가 매우 길고 방문 수요가 제한적이라, 방문 가능 여부 확인이 우선입니다. 현재는 색인보다 문의 기반으로 안내하는 외곽 지역으로 관리합니다."],
   "stations":["함양시외버스터미널"],"auth":["gyeongnam"],"index":False},
  {"slug":"geochang-gun","name":"거창군","h":"거창읍·수승대","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"거창읍, 수승대",
   "over":["거창군은 덕유산 자락의 경남 최북단 내륙 군입니다. 거창읍 시가지와 수승대 관광지, 산간 지역이 생활권을 이룹니다.",
          "산간 외곽 지역이 넓고 이동 거리가 길어 방문 가능 여부를 먼저 확인해야 합니다. 실제 문의 데이터가 확인되기 전까지는 색인보다 안내 위주로 관리하는 지역입니다."],
   "stations":["거창시외버스터미널"],"auth":["gyeongnam"],"index":False},
  {"slug":"hapcheon-gun","name":"합천군","h":"합천읍·해인사","area":"namhae-hadong-west","areaName":"남해·하동·서북부권",
   "life":"합천읍, 해인사, 합천호",
   "over":["합천군은 해인사와 팔만대장경, 합천호로 알려진 경남 내륙의 관광 군입니다. 합천읍 시가지와 해인사 일대, 합천호 주변 관광지가 생활권을 이룹니다.",
          "관광지가 산간에 흩어져 이동 거리가 길고 상시 방문 수요가 제한적입니다. 방문 가능 여부를 먼저 확인하는 지역으로 관리하며, 수요가 확인되면 순차적으로 안내합니다."],
   "stations":["합천시외버스터미널"],"auth":["gyeongnam"],"index":False},
]

# 전체 경남 시·군(내부링크·권역 매칭용)
ALL_GN_CITIES = GN_CITIES + GN_CITIES_2 + GN_CITIES_3


# ------------------------------------------------------------------ 지역 본문 빌더
def region_body(h1, sub, over_paras, zones_label, stations, use_intro,
                near_links, faqs, whw, auth_keys=None):
    over = "".join(f"<p>{esc(p)}</p>" for p in over_paras)
    st = " · ".join(stations)
    body = f"""<section class="section" style="padding-top:2rem">
  <div class="container">
    <span class="eyebrow">지역 안내</span>
    <h1>{esc(h1)}</h1>
    <p class="lead">{esc(sub)}</p>
  </div>
</section>"""
    inner = f"""<div class="prose">
    {over}
    <h3>대표 생활권</h3>
    <p>{esc(zones_label)} 중심으로 이용 환경이 나뉩니다. 같은 지역 안에서도 숙소 형태와 건물 출입 방식이 달라, 정확한 방문 주소를 기준으로 확인하는 것이 안전합니다.</p>
    <h3>가까운 역·터미널</h3>
    <p class="callout">{esc(st)}</p>
    <h3>이용 장소별 확인</h3>
    <p>{esc(use_intro)}</p>
  </div>"""
    body += sec("지역 개요와 이용 기준", inner)
    body += sec("이용 장소에 따라 확인할 내용", taglist(USE_LINKS))
    body += sec("예약 전 확인해야 할 내용", checklist(COMMON_CHECK) +
                '<div style="margin-top:1.2rem">' + taglist(CHECK_LINKS) + "</div>")
    if auth_keys:
        body += sec("교통·이동 참고 자료", auth_note(auth_keys))
    body += sec("자주 묻는 질문", faq_block(faqs), cls="section faq")
    body += sec("Who · How · Why", whw_block(*whw))
    body += sec("관련 지역 보기", taglist(near_links))
    body += ('<section class="section"><div class="container"><div class="notice">'
             '<strong>불법·선정적 서비스 불가</strong> — 본 사이트는 건전한 컨디션·릴랙스 케어 정보만 안내하며, '
             '불법·선정적 서비스는 제공하거나 안내하지 않습니다. '
             '<a href="/check/service-policy/">서비스 이용 기준 보기 →</a></div></div></section>')
    return body


def build_busan_area(a):
    url = f"/busan/area/{a['slug']}/"
    h1 = f"{a['name']} 출장마사지 · 생활권 방문 안내"
    sub = f"{a['zones']} 등 {a['name']} 생활권의 자택·호텔·오피스텔 이용 전 확인사항을 안내합니다."
    desc = f"{a['name']} 출장마사지·홈타이 방문 안내. {a['zones']} 생활권 이용 기준."
    crumbs = [("홈","/"),("부산 생활권","/busan/"),(a['name'],"")]
    faqs = [
        (f"{a['name']}은 어디까지 방문 가능한가요?", "정확한 방문 주소와 생활권, 예약 시간, 이동 기준을 확인한 뒤 안내합니다."),
        (f"{a['name']}에서 호텔·오피스텔 모두 이용할 수 있나요?", "숙소 정책·프런트 확인 방식, 오피스텔 공동현관·관리 규정을 먼저 확인해야 합니다."),
    ] + COMMON_FAQ_TAIL
    whw = (f"{a['name']} 생활권을 직접 확인해 정리한 방문 가능 지역 안내입니다.",
           "시·구 이름이 아닌 실제 방문 주소·숙소 형태·출입 방식 기준으로 정리했습니다.",
           "이용자가 내 위치가 방문 가능 지역인지 빠르게 확인하도록 돕기 위함입니다.")
    body = region_body(h1, sub, a['over'], a['zones'], a['stations'],
                       f"{a['kind']}에 따라 확인할 내용이 달라집니다.",
                       a['near'], faqs, whw, auth_keys=["humetro"])
    page(url, f"{h1}｜{SITE_NAME}", desc, crumbs, body, faqs=faqs,
         area_name=a['name'], priority=0.8)


def build_busan_gu(g):
    url = f"/busan/{g['slug']}/"
    h1 = f"{g['name']} 출장마사지 · {g['h']} 생활권 안내"
    sub = f"부산 {g['name']} {g['h']} 중심 생활권의 방문 가능 지역과 이용 전 확인사항을 안내합니다."
    desc = f"부산 {g['name']} 출장마사지·홈타이 안내. {g['h']} 생활권 이용 기준."
    crumbs = [("홈","/"),("부산 생활권","/busan/"),(g['name'],"")]
    area = next((x for x in BUSAN_AREAS if x['slug']==g['area']), None)
    over = [
        f"부산 {g['name']}은 {g['h']}을(를) 중심으로 생활권이 형성된 지역입니다. 같은 구 안에서도 상권·주거지·업무지구의 이용 환경이 달라, 방문 전 정확한 주소와 생활권을 확인하는 것이 안전합니다.",
        f"{g['name']}은 {area['name'] if area else ''} 생활권과 이어져 있어, 인접 생활권 기준을 함께 확인하면 방문 가능 여부를 판단하기 쉽습니다. 숙소·오피스텔·아파트에 따라 건물 출입 방식과 방문 가능 시간이 다릅니다.",
    ]
    near = [(f"{area['name']} 생활권 안내","/busan/area/"+area['slug']+"/")] if area else []
    near += [("부산 생활권 전체 보기","/busan/"),("경남 권역 안내","/gyeongnam/"),("이용 장소 안내","/use/")]
    faqs = [
        (f"{g['name']}은 구 전체가 방문 가능한가요?", "정확한 방문 주소와 생활권, 예약 시간, 이동 기준을 확인한 뒤 안내합니다."),
    ] + COMMON_FAQ_TAIL
    whw = (f"부산 {g['name']}의 생활권을 확인해 정리한 방문 안내입니다.",
           "실제 방문 주소·숙소 형태 기준으로 정리해 지역명 반복을 피했습니다.",
           "이용자가 방문 가능 지역인지 쉽게 확인하도록 돕기 위함입니다.")
    body = region_body(h1, sub, over, g['h'], g['stations'],
                       "자택·호텔·오피스텔·업무지구에 따라 확인할 내용이 달라집니다.",
                       near, faqs, whw, auth_keys=["humetro"])
    page(url, f"{h1}｜{SITE_NAME}", desc, crumbs, body, faqs=faqs,
         area_name=f"부산 {g['name']}", priority=0.7)


def build_gn_area(a):
    url = f"/gyeongnam/area/{a['slug']}/"
    h1 = f"{a['name']} 출장마사지 · 권역 방문 안내"
    sub = f"{a['zones']} 등 {a['name']}의 도시별 이동 거리와 이용 기준을 안내합니다."
    desc = f"{a['name']} 출장마사지·홈타이 안내. {a['zones']} 이용 기준."
    crumbs = [("홈","/"),("경남 권역","/gyeongnam/"),(a['name'],"")]
    # 권역에 속한 모든 시·군을 데이터에서 도출해 내부링크(색인/noindex 모두 탐색 가능)
    area_cities = [(c['name'], f"/gyeongnam/{c['slug']}/") for c in ALL_GN_CITIES if c['area'] == a['slug']]
    near = area_cities + [("경남 권역 전체 보기","/gyeongnam/"),("부산 생활권 안내","/busan/")]
    faqs = [
        (f"{a['name']}은 전 지역 이용이 가능한가요?", "권역 내 도시 간 이동 거리가 넓어, 방문 주소·예약 시간·이동 기준을 나누어 확인한 뒤 안내합니다."),
    ] + COMMON_FAQ_TAIL
    whw = (f"{a['name']}의 도시별 생활권을 확인해 정리한 안내입니다.",
           "권역 → 도시 → 생활권 순서로 이동 거리와 이용 기준을 정리했습니다.",
           "경남처럼 이동 거리가 넓은 지역에서 방문 가능 여부를 쉽게 판단하도록 돕기 위함입니다.")
    body = region_body(h1, sub, a['over'], a['zones'], ["KTX·시외버스·고속도로 이동 기준"],
                       f"{a['kind']}에 따라 확인할 내용이 달라집니다.",
                       near, faqs, whw, auth_keys=a.get('auth'))
    page(url, f"{h1}｜{SITE_NAME}", desc, crumbs, body, faqs=faqs,
         area_name=a['name'], priority=0.8)


def build_gn_city(c):
    url = f"/gyeongnam/{c['slug']}/"
    h1 = f"{c['name']} 출장마사지 · {c['h']} 이용 안내"
    sub = f"{c['life']} 등 {c['name']} 생활권의 방문 가능 지역과 이용 전 확인사항을 안내합니다."
    desc = f"{c['name']} 출장마사지·홈타이 안내. {c['h']} 생활권 이용 기준."
    crumbs = [("홈","/"),("경남 권역","/gyeongnam/"),(c['areaName'],"/gyeongnam/area/"+c['area']+"/"),(c['name'],"")]
    is_index = c.get('index', True)
    # 같은 권역의 다른 시·군을 인접 링크로(내부링크 강화)
    siblings = [(x['name'], f"/gyeongnam/{x['slug']}/")
                for x in ALL_GN_CITIES if x['area'] == c['area'] and x['slug'] != c['slug']][:3]
    near = [(f"{c['areaName']} 안내","/gyeongnam/area/"+c['area']+"/")] + siblings + \
           [("경남 시·군 전체 보기","/gyeongnam/#si"),("이용 장소 안내","/use/")]
    faqs = [
        (f"{c['name']}은 어디까지 방문 가능한가요?", "정확한 방문 주소와 생활권, 예약 시간, 이동 기준을 확인한 뒤 안내합니다."),
    ] + COMMON_FAQ_TAIL
    whw = (f"{c['name']}의 생활권을 확인해 정리한 방문 안내입니다.",
           "실제 방문 주소·숙소 형태·이동 거리 기준으로 정리했습니다.",
           "이용자가 방문 가능 지역인지 쉽게 확인하도록 돕기 위함입니다.")
    use_intro = "자택·호텔·오피스텔·산업단지 인접 지역에 따라 확인할 내용이 달라집니다."
    if not is_index:
        use_intro = "외곽·산간 지역이 많아 방문 가능 여부와 이동 기준을 먼저 확인해야 합니다."
    body = region_body(h1, sub, c['over'], c['life'], c['stations'], use_intro,
                       near, faqs, whw, auth_keys=c.get('auth'))
    page(url, f"{h1}｜{SITE_NAME}", desc, crumbs, body, faqs=faqs,
         area_name=c['name'], priority=(0.8 if is_index else 0.3), index=is_index)


# ------------------------------------------------------------------ 이용 장소 / 예약 전 확인
USE_PAGES = [
  ("home","자택 이용","자택 방문 시 공동현관·엘리베이터·주차 등 출입 방식과 방문 가능 시간을 미리 확인하면 방문이 매끄럽습니다.",
   ["자택 이용은 가장 일반적인 방문 형태입니다. 아파트·빌라·주택에 따라 공동현관 출입 방식과 주차 여건이 달라, 정확한 주소와 동·호수, 출입 방법을 예약 시 확인합니다.",
    "방문 가능 시간대와 세대 내 준비 사항(공간, 콘센트 등)을 미리 정리하면 예약이 빠르게 진행됩니다."]),
  ("hotel","호텔·숙소 이용","호텔·숙소는 프런트 확인 방식과 객실 출입 정책이 시설마다 다르므로 예약 전 확인이 필요합니다.",
   ["호텔·모텔·게스트하우스 등 숙소는 외부인 방문 정책이 시설마다 다릅니다. 프런트 확인이 필요한 곳, 객실 직접 방문이 가능한 곳을 예약 전에 확인해야 합니다.",
    "체크인 시간과 예약 가능 시간이 겹치는지 확인하고, 객실 번호와 층을 정확히 안내하면 방문이 원활합니다."]),
  ("officetel","오피스텔 이용","오피스텔은 공동현관 비밀번호·엘리베이터 카드·관리 규정에 따라 출입 방식이 달라 사전 확인이 필요합니다.",
   ["오피스텔은 공동현관 비밀번호, 엘리베이터 카드 태그, 방문객 관리 규정이 건물마다 다릅니다. 출입 방식을 예약 시 확인해야 방문이 지연되지 않습니다.",
    "관리 규정상 방문 가능 시간대가 정해진 건물도 있어, 예약 가능 시간과 함께 확인하는 것이 좋습니다."]),
  ("business-district","출장·업무지구 이용","업무지구는 빌딩 보안·방문객 등록 절차가 있어 출입 방식과 방문 가능 시간을 확인해야 합니다.",
   ["업무지구 빌딩은 보안 데스크 방문객 등록, 출입 게이트 등 절차가 있습니다. 출입 방식과 방문 가능 시간을 예약 전에 확인합니다.",
    "출장 방문은 일정이 촘촘한 경우가 많아, 예약 시간과 이동 거리를 함께 조율하면 편리합니다."]),
  ("industrial-area","산업단지 인접 지역 이용","산업단지 인접 지역은 이동 거리와 배후 숙소·오피스텔 여건에 따라 방문 기준을 확인합니다.",
   ["창원·녹산·사천 등 산업단지 배후에는 오피스텔·숙소가 형성되어 있습니다. 이동 거리와 출입 방식에 따라 방문 기준이 달라집니다.",
    "산업단지 인근은 교대 근무 등으로 방문 시간대가 다양해, 예약 가능 시간을 미리 맞추는 것이 좋습니다."]),
  ("station-terminal","KTX·터미널 인접 지역 이용","KTX·터미널 인접 지역은 도착 시간과 예약 가능 시간을 맞추면 이동이 편리합니다.",
   ["부산역·진주역·밀양역 등 KTX역과 시외·고속버스 터미널 인접 지역은 출장·관광 방문이 많습니다. 도착 시간과 예약 가능 시간을 맞추는 것이 중요합니다.",
    "인근 숙소가 관광용인지 업무용인지에 따라 출입 방식이 달라 방문 장소를 정확히 확인합니다."]),
  ("tour-accommodation","관광지·펜션 이용","관광지·펜션·리조트는 프런트 확인 방식과 객실 출입 방법을 예약 전에 확인합니다.",
   ["해운대·광안리·통영·남해 등 관광지의 펜션·리조트는 성수기 방문 정책이 다릅니다. 프런트 확인 방식과 객실 출입 방법을 미리 확인해야 합니다.",
    "관광지 외곽은 이동 거리가 길 수 있어 방문 가능 여부를 먼저 확인하는 것이 좋습니다."]),
  ("night","야간 예약","야간 예약은 방문 가능 시간대와 건물 출입 제한 여부를 함께 확인해야 합니다.",
   ["야간 시간대는 오피스텔·숙소의 출입 제한이나 관리실 운영 여부가 방문에 영향을 줍니다. 방문 가능 시간대를 예약 시 확인합니다.",
    "야간 이동은 거리와 시간에 따라 기준이 달라질 수 있어 사전 확인이 필요합니다."]),
  ("outer-area","외곽 지역 이용","외곽 지역은 방문 가능 여부와 추가 이동 기준을 예약 전에 반드시 확인합니다.",
   ["기장·정관, 거제·통영, 남해·하동 등 외곽 지역은 도심에서 이동 거리가 깁니다. 방문 가능 여부와 추가 이동 기준을 먼저 확인해야 합니다.",
    "외곽 지역은 예약 시간대에 따라 방문 가능 여부가 달라질 수 있어 여유 있게 문의하는 것이 좋습니다."]),
]

CHECK_PAGES = [
  ("address","방문 주소 확인","방문 주소는 부산/경남과 세부 생활권까지 정확히 확인해야 방문 가능 여부를 판단할 수 있습니다.",
   ["방문 주소는 시·구·동뿐 아니라 세부 생활권, 건물명, 동·호수까지 정확히 확인해야 합니다. 같은 지역명이라도 생활권에 따라 이동 기준이 다릅니다."]),
  ("building-access","건물 출입 방식","공동현관·엘리베이터·보안 데스크 등 건물 출입 방식을 예약 전에 확인합니다.",
   ["공동현관 비밀번호, 엘리베이터 카드, 보안 데스크 방문객 등록 등 출입 방식은 건물마다 다릅니다. 예약 시 미리 확인하면 방문이 지연되지 않습니다."]),
  ("hotel-policy","호텔·숙소 정책","호텔·숙소의 외부인 방문 정책과 프런트 확인 방식을 예약 전에 확인합니다.",
   ["숙소는 외부인 방문 정책이 시설마다 다릅니다. 프런트 확인이 필요한지, 객실 직접 방문이 가능한지 예약 전에 확인해야 합니다."]),
  ("officetel-rule","오피스텔 관리 규정","오피스텔의 공동현관·엘리베이터·방문 시간 규정을 예약 전에 확인합니다.",
   ["오피스텔은 방문객 관리 규정과 방문 가능 시간대가 건물마다 다릅니다. 공동현관·엘리베이터 출입 방식과 함께 확인해야 합니다."]),
  ("travel-fee","추가 이동비 기준","외곽·장거리 지역은 이동 거리와 예약 시간에 따라 추가 이동 기준이 달라질 수 있습니다.",
   ["60·90·120분 코스 기준 요금은 지역과 관계없이 동일합니다. 다만 외곽·장거리 지역은 이동 거리·예약 시간대에 따라 상담 시 최종 확인됩니다. 근거 없는 최저가·무조건 가능 같은 표현은 사용하지 않습니다."]),
  ("time","예약 가능 시간","예약 가능 시간과 방문 가능 시간대를 미리 확인하면 일정 조율이 쉽습니다.",
   ["예약 가능 시간과 실제 방문 가능 시간대는 지역·건물 사정에 따라 다를 수 있습니다. 야간 방문은 출입 제한 여부를 함께 확인합니다."]),
  ("change-policy","예약 변경 기준","예약 변경·취소 기준을 미리 확인하면 일정 변동에 대응하기 쉽습니다.",
   ["예약 변경·취소는 방문 시간과 이동 준비에 영향을 줍니다. 변경이 필요한 경우 가능한 한 빨리 문의해 주시면 조율이 원활합니다."]),
  ("privacy","개인정보 처리 기준","예약 확인과 연락에 필요한 최소한의 개인정보만 확인하고 목적 외로 사용하지 않습니다.",
   ["예약 확인과 연락에 필요한 최소 정보(연락처, 방문 주소 등)만 확인하며, 목적 외로 사용하거나 제3자에게 제공하지 않습니다. 개인정보 보호와 관련한 일반 기준은 공식 기관 자료로도 확인할 수 있습니다."]),
  ("service-policy","불법·선정적 서비스 불가 안내","본 사이트는 건전한 컨디션·릴랙스 케어 정보만 안내하며 불법·선정적 서비스는 제공하지 않습니다.",
   ["본 사이트는 건전한 컨디션·릴랙스 케어에 대한 지역 정보만 안내합니다. 불법·선정적 서비스는 제공하거나 안내하지 않으며, 관련 문의에는 응하지 않습니다."]),
  ("customer-notice","고객 유의사항","예약 전 방문 주소·출입 방식·예약 시간·이용 기준을 확인하면 방문이 원활합니다.",
   ["예약 전 방문 주소, 건물 출입 방식, 예약 가능 시간, 이용 기준을 확인해 주시면 방문이 원활합니다. 허위 정보나 과장 표현 없이 있는 그대로 안내드립니다."]),
]


def simple_content_page(url, h1, sub, desc, crumbs, paras, related, area_name,
                        auth_keys=None, priority=0.6):
    over = "".join(f"<p>{esc(p)}</p>" for p in paras)
    body = f"""<section class="section" style="padding-top:2rem"><div class="container">
      <span class="eyebrow">안내</span><h1>{esc(h1)}</h1><p class="lead">{esc(sub)}</p></div></section>"""
    body += sec("안내 내용", f'<div class="prose">{over}</div>')
    if auth_keys:
        body += sec("참고 자료", auth_note(auth_keys))
    body += sec("함께 확인하면 좋은 안내", taglist(related))
    body += ('<section class="section"><div class="container"><div class="notice">'
             '<strong>불법·선정적 서비스 불가</strong> — 건전한 케어 정보만 안내합니다. '
             '<a href="/check/service-policy/">이용 기준 보기 →</a></div></div></section>')
    page(url, f"{h1}｜{SITE_NAME}", desc, crumbs, body, area_name=area_name, priority=priority)


def build_use_pages():
    idx_cards = [(f"{name}", intro, f"/use/{slug}/") for slug,name,intro,_ in USE_PAGES]
    body = f"""<section class="section" style="padding-top:2rem"><div class="container">
      <span class="eyebrow">이용 장소</span><h1>이용 장소에 따라 확인할 내용이 다릅니다</h1>
      <p class="lead">자택·호텔·오피스텔·업무지구·산업단지·터미널·관광지 등 방문 장소별 확인 사항을 안내합니다.</p></div></section>"""
    body += sec("이용 장소별 안내", card_grid(idx_cards, cols=3))
    body += sec("예약 전 확인 안내", taglist(CHECK_LINKS))
    page("/use/", f"이용 장소별 확인 안내｜{SITE_NAME}",
         "부산·경남 출장마사지 이용 장소별 확인 사항 안내. 자택·호텔·오피스텔 기준.",
         [("홈","/"),("이용 장소","")], body, area_name="부산·경남", priority=0.6)
    for slug,name,intro,paras in USE_PAGES:
        related = [(n2,f"/use/{s2}/") for s2,n2,_,_ in USE_PAGES if s2!=slug][:5] + [("예약 전 확인 안내","/check/")]
        simple_content_page(f"/use/{slug}/", f"{name} 기준 안내",
            intro, f"부산·경남 {name} 출장마사지 이용 기준 안내. 방문 전 확인 사항.",
            [("홈","/"),("이용 장소","/use/"),(name,"")], paras, related, "부산·경남",
            auth_keys=(["korail"] if slug=="station-terminal" else None))


def build_check_pages():
    idx_cards = [(name, intro, f"/check/{slug}/") for slug,name,intro,_ in CHECK_PAGES]
    body = f"""<section class="section" style="padding-top:2rem"><div class="container">
      <span class="eyebrow">예약 전 확인</span><h1>예약 전 확인해야 할 내용</h1>
      <p class="lead">방문 주소·건물 출입 방식·예약 시간·이용 기준 등 예약 전 확인 사항을 안내합니다.</p></div></section>"""
    body += sec("예약 전 확인 항목", card_grid(idx_cards, cols=3))
    body += sec("이용 장소 안내", taglist(USE_LINKS))
    page("/check/", f"예약 전 확인 안내｜{SITE_NAME}",
         "부산·경남 출장마사지 예약 전 확인 안내. 주소·출입·시간·이용 기준.",
         [("홈","/"),("예약 전 확인","")], body, area_name="부산·경남", priority=0.6)
    for slug,name,intro,paras in CHECK_PAGES:
        related = [(n2,f"/check/{s2}/") for s2,n2,_,_ in CHECK_PAGES if s2!=slug][:5] + [("이용 장소 안내","/use/")]
        simple_content_page(f"/check/{slug}/", f"{name}",
            intro, f"부산·경남 출장마사지 {name}. 예약 전 확인 사항 안내.",
            [("홈","/"),("예약 전 확인","/check/"),(name,"")], paras, related, "부산·경남",
            auth_keys=(["pipc"] if slug=="privacy" else None))


# ------------------------------------------------------------------ 메인 / 부산 / 경남 / 문의
def build_index():
    hero = f"""<section class="hero"><div class="container">
      <span class="eyebrow">부산·경남 출장마사지 지역 안내</span>
      <h1>부산·경남 출장마사지 · 생활권별 방문 가능 지역 안내</h1>
      <p class="lead">해운대·서면·광안리·부산역·창원·김해·양산·거제·진주 등 부산·경남 주요 생활권과 자택·호텔·오피스텔 이용 전 확인사항을 안내합니다.</p>
      <div class="cta-row">
        <a class="btn btn-primary btn-lg" href="/busan/">부산 생활권 보기</a>
        <a class="btn btn-ghost btn-lg" href="/gyeongnam/">경남 권역 보기</a>
        <a class="btn btn-ghost btn-lg" href="/use/">이용 장소 보기</a>
      </div></div></section>"""
    intro = sec("부산·경남은 지역명보다 생활권 확인이 먼저입니다",
        '<div class="prose"><p>부산은 해안 관광지, 도심 상권, 주거지, 업무지구, 서부산 산업권이 서로 다릅니다. 경남은 도시 간 이동 거리가 넓고, 창원·김해·양산 같은 생활권과 거제·통영·진주 같은 권역의 이용 기준이 다릅니다.</p><p>따라서 단순히 시·군 이름만 보는 것이 아니라 실제 방문 주소, 가까운 생활권, 숙소 형태, 건물 출입 방식, 예약 가능 시간을 함께 확인해야 합니다.</p></div>')
    b_cards = [(a['name'], a['zones'], f"/busan/area/{a['slug']}/") for a in BUSAN_AREAS]
    busan_sec = sec("부산 주요 생활권 안내", card_grid(b_cards, cols=4))
    g_cards = [(a['name'], a['zones'], f"/gyeongnam/area/{a['slug']}/") for a in GN_AREAS]
    gn_sec = sec("경남 주요 권역 안내", card_grid(g_cards, cols=3))
    use_sec = sec("이용 장소에 따라 확인할 내용이 다릅니다", taglist(USE_LINKS))
    check_sec = sec("예약 전 확인해야 할 내용", checklist(COMMON_CHECK) +
                    '<div style="margin-top:1.2rem">' + taglist(CHECK_LINKS) + "</div>")
    faqs = [
        ("부산 전 지역 방문이 가능한가요?", "실제 방문 주소, 생활권, 예약 시간, 이동 기준을 확인한 뒤 안내합니다."),
        ("경남도 전 지역 이용이 가능한가요?", "경남은 시·군 간 이동 거리가 넓어 창원·김해·양산·진주·거제 등 주요 지역과 외곽 지역의 기준을 나누어 확인합니다."),
        ("부산은 구별로 찾는 것이 좋나요, 생활권으로 찾는 것이 좋나요?", "같은 구 안에서도 해운대·센텀, 서면·전포처럼 이용 환경이 달라 생활권과 구·군을 함께 확인하는 것이 좋습니다."),
        ("호텔이나 숙소에서도 이용할 수 있나요?", "숙소 정책, 객실 출입 가능 여부, 프런트 확인 방식 등을 먼저 확인해야 합니다."),
        ("외곽 지역은 추가 이동비가 있나요?", "지역·거리·예약 시간·이동 가능 여부에 따라 달라질 수 있어 사전 확인이 필요합니다."),
    ] + COMMON_FAQ_TAIL
    faq_sec = sec("자주 묻는 질문", faq_block(faqs), cls="section faq")
    whw_sec = sec("Who · How · Why", whw_block(
        "부산·경남 생활권을 직접 확인해 정리한 지역 안내 사이트입니다.",
        "지역명 반복이 아니라 실제 방문 주소·생활권·이용 기준 중심으로 구성했습니다.",
        "이용자가 내 위치가 방문 가능 지역인지 쉽게 확인하도록 돕기 위함입니다."))
    body = hero + intro + busan_sec + gn_sec + use_sec + check_sec + faq_sec + whw_sec
    page("/", f"부산·경남 출장마사지｜해운대·서면·창원·김해 홈타이 지역 안내",
         "부산·경남 출장마사지·홈타이 생활권별 방문 가능 지역과 이용 기준 안내.",
         [("홈","")], body, faqs=faqs, area_name="부산·경남", priority=1.0)


def build_busan_index():
    hero = f"""<section class="hero"><div class="container">
      <span class="eyebrow">부산</span>
      <h1>부산 출장마사지 · 생활권과 16개 구·군 안내</h1>
      <p class="lead">해운대·센텀, 서면·전포, 광안리·수영, 부산역·남포 등 부산 8개 생활권과 16개 구·군의 방문 가능 지역을 안내합니다.</p>
      <div class="cta-row"><a class="btn btn-primary btn-lg" href="#area">생활권 보기</a>
      <a class="btn btn-ghost btn-lg" href="#gu">구·군 보기</a></div></div></section>"""
    a_cards = [(a['name'], a['zones'], f"/busan/area/{a['slug']}/") for a in BUSAN_AREAS]
    gu_cards = [(g['name'], g['h'], f"/busan/{g['slug']}/") for g in BUSAN_GU]
    body = hero
    body += sec("부산 주요 생활권", card_grid(a_cards, cols=4), hid="area")
    body += sec("부산 16개 구·군 안내", card_grid(gu_cards, cols=4), hid="gu")
    body += sec("경남도 함께 확인하세요", taglist(
        [(a['name'], f"/gyeongnam/area/{a['slug']}/") for a in GN_AREAS]))
    page("/busan/", f"부산 출장마사지 생활권·구·군 안내｜{SITE_NAME}",
         "부산 출장마사지·홈타이 8개 생활권과 16개 구·군 방문 가능 지역 안내.",
         [("홈","/"),("부산","")], body, area_name="부산", priority=0.9)


def build_gn_index():
    hero = f"""<section class="hero"><div class="container">
      <span class="eyebrow">경남</span>
      <h1>경남 출장마사지 · 권역과 시·군 안내</h1>
      <p class="lead">창원·김해·양산권, 진주·사천권, 거제·통영·고성권 등 경남 5개 권역과 핵심 시·군의 방문 가능 지역을 안내합니다.</p>
      <div class="cta-row"><a class="btn btn-primary btn-lg" href="#area">권역 보기</a>
      <a class="btn btn-ghost btn-lg" href="#si">시·군 보기</a></div></div></section>"""
    a_cards = [(a['name'], a['zones'], f"/gyeongnam/area/{a['slug']}/") for a in GN_AREAS]
    core_cards = [(c['name'], c['h'], f"/gyeongnam/{c['slug']}/") for c in (GN_CITIES + GN_CITIES_2)]
    outer_links = [(c['name'], f"/gyeongnam/{c['slug']}/") for c in GN_CITIES_3]
    body = hero
    body += sec("경남 주요 권역", card_grid(a_cards, cols=3), hid="area")
    body += sec("경남 시·군 안내", card_grid(core_cards, cols=4),
                hid="si", lead="검색 수요와 방문 가능성이 높은 핵심 시·군부터 안내합니다. 각 지역은 실제 방문 가능 여부와 이동 기준을 함께 확인합니다.")
    body += sec("외곽·산간 지역 (방문 가능 여부 확인 후 안내)",
                taglist(outer_links),
                lead="의령·산청·함양·거창·합천 등 외곽 산간 지역은 이동 거리가 길어, 실제 문의 데이터를 확인한 뒤 순차적으로 안내합니다.")
    body += sec("부산도 함께 확인하세요", taglist(
        [(a['name'], f"/busan/area/{a['slug']}/") for a in BUSAN_AREAS]))
    page("/gyeongnam/", f"경남 출장마사지 권역·시·군 안내｜{SITE_NAME}",
         "경남 출장마사지·홈타이 5개 권역과 핵심 시·군 방문 가능 지역 안내.",
         [("홈","/"),("경남","")], body, area_name="경남", priority=0.9)


# ------------------------------------------------------------------ 운영 기준(E-E-A-T · 비도어웨이)
ABOUT_PAGES = [
  ("how-we-work", "예약·방문 운영 방식",
   "전화·텔레그램 예약 접수부터 방문 주소·생활권·시간 확인, 이동 기준 안내까지의 운영 방식을 정리했습니다.",
   ["간다GO는 부산·경남 지역의 방문 케어 예약을 전화(0508-202-4719)와 텔레그램으로 접수합니다. 예약 시에는 방문 주소와 세부 생활권, 건물 출입 방식, 예약 가능 시간을 함께 확인해 방문 가능 여부를 판단합니다.",
    "코스는 60·90·120분으로 운영하며, 기준 요금(90,000 / 150,000 / 180,000원)은 지역과 관계없이 동일합니다. 외곽·장거리 지역은 이동 거리와 예약 시간대에 따라 상담 시 최종 확인되며, 근거 없는 최저가·무조건 가능 같은 표현은 사용하지 않습니다.",
    "예약 변경이 필요한 경우 가능한 한 빨리 연락 주시면 방문 시간과 이동 준비를 조율합니다. 야간·외곽 방문은 건물 출입 제한과 이동 가능 여부를 미리 확인합니다."],
   ["korail", "humetro"]),
  ("editorial", "지역 정보 작성·검수 기준",
   "부산·경남 지역 정보를 어떤 자료로 작성하고 어떻게 검수하는지, 무엇을 싣지 않는지 정리했습니다.",
   ["이 사이트의 지역 안내는 부산·경남의 실제 생활권 구성, 교통 거점, 숙소·오피스텔·업무지구 분포를 직접 확인해 정리한 내용입니다. 지역명만 바꾼 복제 문장이나 검색엔진용 반복 페이지는 만들지 않습니다.",
    "작성 과정에서 문장 정리에 AI 도구를 보조로 활용하더라도, 지역 사실 관계와 이용 기준은 운영자가 직접 검수해 게시합니다. 구글이 안내하는 '누가·어떻게·왜 만들었는가' 기준에 따라, 결과물의 정확성과 실사용 가치를 우선합니다.",
    "허위 후기, 조작된 별점, 실제 매장이 없는 상태의 매장형 표기, 본문에 없는 FAQ 마크업 등 사용자를 오인하게 하는 요소는 사용하지 않습니다. 요금·FAQ 등 구조화 데이터는 페이지에 실제로 보이는 내용과 일치시킵니다."],
   None),
  ("coverage", "안내 지역 선정·색인 기준",
   "어떤 지역을 우선 안내하고, 어떤 외곽 지역을 방문 확인 후 안내하는지 판단 기준을 공개합니다.",
   ["부산은 16개 구·군과 8개 생활권, 경남은 5개 권역과 18개 시·군을 기준으로 안내합니다. 실제 방문 가능성과 검색 수요가 높은 핵심 지역부터 상세히 안내하고, 이동 거리가 길거나 수요가 제한적인 외곽 산간 지역은 방문 가능 여부를 확인한 뒤 순차적으로 안내합니다.",
    "품질과 실수요가 확인되기 전의 외곽 지역(의령·산청·함양·거창·합천 등)은 색인에서 제외해 관리합니다. 이는 얇거나 중복된 지역 페이지를 양산하지 않기 위한 기준으로, 구글의 스팸·도어웨이 정책을 따르기 위함입니다.",
    "각 지역 페이지는 지역 개요, 대표 생활권, 가까운 역·터미널, 이용 장소별 확인 사항, 예약 전 체크리스트를 갖춘 고유 본문으로 작성합니다."],
   None),
  ("compliance", "법규 준수·서비스 원칙",
   "불법·선정적 서비스 불가, 개인정보 최소 수집, 과장 표현 금지 등 운영 원칙을 정리했습니다.",
   ["간다GO는 건전한 컨디션·릴랙스 케어에 대한 지역 정보만 안내합니다. 불법·선정적 서비스는 제공하거나 안내하지 않으며, 관련 문의에는 응하지 않습니다.",
    "개인정보는 예약 확인과 연락에 필요한 최소 정보만 확인하며, 목적 외로 사용하거나 제3자에게 제공하지 않습니다. 개인정보 보호에 관한 일반 기준은 공식 기관 자료로도 확인할 수 있습니다.",
    "'최고', '1위', '무조건 가능', '최저가 보장' 등 근거 없는 표현과 선정적 표현은 사용하지 않습니다. 있는 그대로의 이용 기준을 안내하는 것을 원칙으로 합니다."],
   ["pipc"]),
]


def build_about_pages():
    # 허브(운영 기준)
    hub_cards = [(name, sub, f"/about/{slug}/") for slug, name, sub, _, _ in ABOUT_PAGES]
    body = f"""<section class="hero"><div class="container">
      <span class="eyebrow">운영 기준</span><h1>간다GO 소개와 운영 기준</h1>
      <p class="lead">간다GO가 어떤 기준으로 부산·경남 출장마사지 지역 정보를 안내하고, 예약·방문을 운영하는지 정리했습니다.</p>
      <div class="cta-row"><a class="btn btn-primary btn-lg" href="{esc(TEL_HREF)}">전화예약 {esc(PHONE)}</a>
      <a class="btn btn-ghost btn-lg" href="/contact/">문의하기</a></div></div></section>"""
    body += sec("간다GO는 이런 사이트입니다",
        '<div class="prose"><p>간다GO는 부산·경남의 출장마사지·홈타이 방문 케어를 안내하는 지역 정보 사이트입니다. 해운대·서면·창원·김해 등 주요 생활권과 자택·호텔·오피스텔 이용 기준을 정리해, 이용자가 자신의 위치가 방문 가능 지역인지 쉽게 확인하도록 돕습니다.</p>'
        '<p class="muted">상호 <strong>간다GO</strong> · 전화예약 ' + esc(PHONE) + ' · 부산·경남 지역 안내 운영. 광고성 반복 페이지가 아닌, 실제 지역 특성에 기반한 안내를 지향합니다.</p></div>')
    body += sec("운영 기준 자세히 보기", card_grid(hub_cards, cols=2))
    body += sec("Who · How · Why", whw_block(
        "부산·경남 지역을 직접 확인해 정보를 정리·운영하는 지역 안내 사이트입니다.",
        "지역명 반복이 아니라 실제 생활권·교통·이용 기준 중심으로 작성하고 사람이 검수합니다.",
        "이용자가 방문 가능 지역과 이용 기준을 정확히 확인하도록 돕기 위함입니다."))
    body += sec("함께 확인하면 좋은 안내", taglist(
        [("예약 전 확인 안내","/check/"),("이용 장소 안내","/use/"),
         ("불법·선정적 서비스 불가 안내","/check/service-policy/"),("개인정보 처리 기준","/check/privacy/")]))
    page("/about/", f"간다GO 소개·운영 기준｜{SITE_NAME}",
         "간다GO 부산·경남 출장마사지 안내 운영 기준·소개. 작성·색인·서비스 원칙.",
         [("홈","/"),("운영 기준","")], body, area_name="부산·경남", priority=0.6)
    # 하위 5개 중 4개(허브 제외) + 각 페이지
    for slug, name, sub, paras, auth in ABOUT_PAGES:
        related = [(n2, f"/about/{s2}/") for s2, n2, _, _, _ in ABOUT_PAGES if s2 != slug]
        related += [("예약 전 확인 안내","/check/"),("문의하기","/contact/")]
        simple_content_page(f"/about/{slug}/", name, sub,
            f"간다GO 부산·경남 출장마사지 {name}. 운영·작성·서비스 기준 안내.",
            [("홈","/"),("운영 기준","/about/"),(name,"")], paras, related,
            "부산·경남", auth_keys=auth, priority=0.5)


def build_contact():
    body = f"""<section class="hero"><div class="container">
      <span class="eyebrow">문의하기</span><h1>예약·제작·제휴 문의</h1>
      <p class="lead">전화예약 또는 텔레그램으로 편하게 문의해 주세요. 방문 가능 지역과 이용 기준을 안내해 드립니다.</p>
      <div class="cta-row">
        <a class="btn btn-primary btn-lg" href="{esc(TEL_HREF)}">전화예약 {esc(PHONE)}</a>
        <a class="btn btn-primary btn-lg" href="{esc(TELEGRAM_BUILD)}" target="_blank" rel="noopener">✈ 웹사이트 제작문의</a>
        <a class="btn btn-primary btn-lg" href="{esc(TELEGRAM_PARTNER)}" target="_blank" rel="noopener">✈ 제휴문의</a>
      </div></div></section>"""
    body += sec("문의 안내", f'<div class="prose"><p>상호 <strong>{esc(SITE_NAME)}</strong> · 전화예약 <a class="tel" href="{esc(TEL_HREF)}">{esc(PHONE)}</a></p><p class="muted">웹사이트 제작문의와 제휴문의는 상단 텔레그램 버튼으로 연결됩니다. 불법·선정적 서비스 관련 문의에는 응하지 않습니다.</p></div>')
    body += sec("예약 전 확인", taglist(CHECK_LINKS))
    page("/contact/", f"문의하기｜{SITE_NAME}",
         "간다GO 부산·경남 출장마사지 문의. 전화예약·제작·제휴 텔레그램 안내.",
         [("홈","/"),("문의하기","")], body, area_name="부산·경남", priority=0.5)


# ------------------------------------------------------------------ sitemap / robots
def write_sitemap():
    urls = ""
    for path, prio, indexed in PAGES:
        if not indexed:
            continue
        urls += (f"<url><loc>{BASE_URL}{path}</loc>"
                 f"<changefreq>weekly</changefreq><priority>{prio:.1f}</priority></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")


def main():
    build_index()
    build_busan_index()
    build_gn_index()
    for a in BUSAN_AREAS: build_busan_area(a)
    for g in BUSAN_GU: build_busan_gu(g)
    for a in GN_AREAS: build_gn_area(a)
    for c in ALL_GN_CITIES: build_gn_city(c)
    build_use_pages()
    build_check_pages()
    build_about_pages()
    build_contact()
    write_sitemap()
    print(f"생성 완료: {len(PAGES)} 페이지")
    for path, prio, indexed in PAGES:
        print(f"  {'[idx]' if indexed else '[nox]'} {path}")


if __name__ == "__main__":
    main()
