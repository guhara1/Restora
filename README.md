# 간다GO · 부산·경남 출장마사지 지역 안내

프리미엄 팔레트 + Pretendard 토큰 시스템으로 구성한 정적 지역 안내 사이트입니다.
모든 페이지에 **오렌지 텔레그램 문의 버튼 푸터 · 가격표(60·90·120분) · JSON-LD 스키마 ·
≤80자 메타 디스크립션 · 내부링크(롱테일 앵커)** 가 자동 적용됩니다.

## 생성 방법
```bash
python3 build.py      # 루트에 62개 정적 HTML + sitemap.xml + robots.txt 생성
```
정적 파일이므로 그대로 웹 서버 루트에 올리면 됩니다. (경로가 절대경로 `/assets/...`
이므로 로컬 확인 시 `python3 -m http.server` 로 서빙하세요. `file://` 로는 CSS가 안 붙습니다.)

## 교체 지점 (배포 전 확인)
`build.py` 상단 상수만 바꾸면 전 페이지에 반영됩니다.

| 상수 | 현재 값 | 설명 |
|---|---|---|
| `TELEGRAM_BUILD` | `https://t.me/gandago` | 웹사이트 **제작문의** 버튼 링크 (임시값 → 실제 아이디로 교체) |
| `TELEGRAM_PARTNER` | `https://t.me/gandago` | **제휴문의** 버튼 링크 |
| `BASE_URL` | `https://ganda-go.com` | canonical·og·schema·sitemap 도메인 |
| `PHONE` / `TEL_HREF` | `0508-202-4719` | 전화예약 번호 |
| `PRICING` | 90,000 / 150,000 / 180,000 | 코스별 요금(가격표 + Offer 스키마 동시 반영) |

## 디자인 토큰 / 컴포넌트
- `assets/css/tokens.css` — 프리미엄 팔레트(딥 네이비 + 오렌지) · Pretendard · 반경/그림자/타이포 토큰
- `assets/css/style.css` — 컴포넌트 + 오버레이(hero/card/price 글로우 등)
- `assets/js/site.js` — 모바일 내비 토글

## SEO / 스키마 원칙 (구글 정책 준수)
- 스키마: `Organization` · `WebSite` · `WebPage` · `BreadcrumbList` · `Service`+`AggregateOffer` · `FAQPage`
  (본문에 실제 보이는 요금·FAQ만 마크업)
- **미사용**: 가짜 `Review`/`AggregateRating`, 실제 매장 없는 `LocalBusiness` — 정책 위반 회피
- 메타 디스크립션 전 페이지 80자 이내(빌드 시 강제 검증)
- 내부링크는 "해운대·센텀 생활권 보기"류 서술형 롱테일 앵커, 교통 정보는 부산교통공사·코레일 등
  권위 기관으로 아웃바운드(`rel="noopener nofollow"`)
- 금지 표현(최고·1위·무조건 가능·최저가 등) 미사용, 도어웨이/얇은 페이지 지양
- **도어웨이 회피**: 경남 18개 시·군 전 페이지 고유 본문(지역명 스왑 없음, 빌드 시 본문 해시 검증).
  외곽 산간 5개 군(의령·산청·함양·거창·합천)은 실수요 확인 전까지 `noindex`(sitemap 제외)로 관리.
  개별 역세권/출구·노선 페이지는 도어웨이 위험이 커 만들지 않고 교통 정보는 본문 내 권위 기관 링크로 처리

## 구조
```
/                         부산·경남 메인
/busan/                   부산 생활권 + 16개 구·군 허브
/busan/area/<8개 생활권>/
/busan/<16개 구·군>/
/gyeongnam/               경남 권역 + 시·군 허브
/gyeongnam/area/<5개 권역>/
/gyeongnam/<시·군 18개>/    핵심 8개 시 + 2차 색인 5개 군(함안·창녕·고성·하동·남해)
                          + 3차 5개 군(의령·산청·함양·거창·합천, noindex)
/use/<9개 이용 장소>/
/check/<10개 예약 전 확인>/
/contact/                 문의(전화·제작·제휴)
```
