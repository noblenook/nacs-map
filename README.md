# NACS

한국 공공 충전소 데이터(한국환경공단)의 NACS 충전기(chgerType 10: DC콤보+NACS)와
테슬라 슈퍼차저(supercharge.info 커뮤니티 데이터)를 지도에 보여주는 개인용 앱.

## 기능
- 상단 버튼으로 슈퍼차저 / NACS 운영사(워터·채비·SK일렉링크·SK시그넷·펌프킨) 선택
- 출발지(기본: 내 위치)·목적지 검색 → 경로 N km 이내 충전소만 표시
  - 슈퍼차저: 곳 수와 총 기수 (실시간 빈자리 정보 없음)
  - NACS: 곳 수와 충전가능/전체 기수
- 안드로이드: 테스맵·카카오맵·네이버지도에서 장소 '공유' → 이 앱 선택 시 바로 경로 안내
- 카카오 REST API 키 필요: 설정(⚙)에서 입력하거나, `kakao_key.txt` 로 APK 에 내장

## 데이터
- `python fetch_nacs.py` — 전체 목록 새로 받기 (API 약 53회, 3~5분)
- `python fetch_nacs.py --status` — 최근 10분 상태 변경만 반영 (API 2~3회)
- 인증키: `key.txt` 또는 환경변수 `DATA_GO_KR_KEY` (git 제외)
- GitHub Actions(`.github/workflows/update.yml`)가 10분마다 상태, 매일 03:00 전체 목록 갱신 → 저장소 Secret `DATA_GO_KR_KEY` 필요

## 실시간 상태
- 웹/앱 모두 GitHub 의 `nacs.json` 을 2~3분마다 다시 읽음
- APK 는 빌드 때 `key.txt` 의 키가 들어가, 환경부 API 에서 최근 5분 상태를 직접 받아 즉시 반영

## Android APK 빌드
```
npm install
npm run sync          # index.html → www/ (키 주입) → android 동기화
cd android && gradlew.bat assembleDebug
```
결과: `android/app/build/outputs/apk/debug/app-debug.apk`
(JAVA_HOME = Android Studio 의 jbr, ANDROID_HOME = Android SDK)
