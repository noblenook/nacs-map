"""
한국환경공단 전기자동차 충전소 정보 API에서 NACS 충전기만 골라 nacs.json 으로 저장합니다.

사용법:
  1) data.go.kr 에서 "한국환경공단_전기자동차 충전소 정보" 활용신청 → 인증키(Decoding) 복사
  2) 이 폴더에 key.txt 로 저장 (또는 환경변수 DATA_GO_KR_KEY)
  3) python fetch_nacs.py

옵션:
  --codes 09,10   NACS 로 간주할 chgerType 코드 (기본 09,10)
  --types         전체 chgerType 분포만 출력하고 종료 (코드 확인용)
  --status        전체를 다시 받지 않고 nacs.json 의 충전 상태만 최근 변경분으로 갱신 (API 호출 2~3회)
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

API = "https://apis.data.go.kr/B552584/EvCharger/"
ROWS = 9999
HERE = os.path.dirname(os.path.abspath(__file__))


def load_key():
    key = os.environ.get("DATA_GO_KR_KEY")
    path = os.path.join(HERE, "key.txt")
    if not key and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            key = f.read().strip()
    if not key:
        sys.exit("인증키가 없습니다. key.txt 를 만들거나 DATA_GO_KR_KEY 를 설정하세요.")
    # Encoding 키를 넣어도 동작하도록 한 번 디코딩
    return urllib.parse.unquote(key)


def fetch_page(key, page, op="getChargerInfo", **extra):
    q = urllib.parse.urlencode(
        {"serviceKey": key, "pageNo": page, "numOfRows": ROWS, "dataType": "JSON", **extra}
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"{API}{op}?{q}", timeout=120) as r:
                body = r.read().decode("utf-8")
            return parse(body)
        except Exception as e:  # 네트워크 오류 등은 재시도
            if attempt == 3:
                raise
            print(f"  재시도 {attempt + 1}: {e}")
            time.sleep(3 * (attempt + 1))


def parse(body):
    body = body.strip()
    if body.startswith("{"):
        d = json.loads(body)
        if d.get("resultCode") not in (None, "00"):
            raise RuntimeError(f"API 오류: {d.get('resultCode')} {d.get('resultMsg')}")
        items = (d.get("items") or {}).get("item") or []
        if isinstance(items, dict):
            items = [items]
        return int(d.get("totalCount") or 0), items
    root = ET.fromstring(body)
    code = root.findtext(".//resultCode") or root.findtext(".//returnReasonCode")
    if code not in (None, "00"):
        msg = root.findtext(".//resultMsg") or root.findtext(".//returnAuthMsg")
        raise RuntimeError(f"API 오류: {code} {msg}")
    total = int(root.findtext(".//totalCount") or 0)
    items = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("item")]
    return total, items


def now():
    # GitHub Actions(UTC)에서도 한국 시각으로 기록
    from datetime import timedelta, timezone
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")


def update_status(key):
    path = os.path.join(HERE, "nacs.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    index = {(s["id"], c["id"]): c for s in data["stations"] for c in s["chargers"]}
    total, items = fetch_page(key, 1, "getChargerStatus", period=10)
    for p in range(2, max(1, -(-total // ROWS)) + 1):
        items.extend(fetch_page(key, p, "getChargerStatus", period=10)[1])
    changed = 0
    for it in items:
        c = index.get((it.get("statId"), it.get("chgerId")))
        if c and (c["stat"], c["upd"]) != (str(it.get("stat")), it.get("statUpdDt", "")):
            c["stat"], c["upd"] = str(it.get("stat")), it.get("statUpdDt", "")
            changed += 1
    data["generatedAt"] = now()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"최근 10분 변경 {len(items):,}건 중 NACS {changed}건 반영")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", default="09,10")
    ap.add_argument("--types", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        return update_status(load_key())
    nacs_codes = {c.strip().zfill(2) for c in args.codes.split(",") if c.strip()}

    key = load_key()
    total, items = fetch_page(key, 1)
    pages = max(1, -(-total // ROWS))
    print(f"전체 충전기 {total:,}대, {pages}페이지")
    all_items = list(items)
    for p in range(2, pages + 1):
        print(f"  {p}/{pages} 페이지 받는 중...")
        all_items.extend(fetch_page(key, p)[1])

    hist = {}
    for it in all_items:
        t = str(it.get("chgerType", "")).zfill(2)
        hist[t] = hist.get(t, 0) + 1
    print("chgerType 분포:", ", ".join(f"{k}={v:,}" for k, v in sorted(hist.items())))
    if args.types:
        return

    stations = {}
    for it in all_items:
        if str(it.get("chgerType", "")).zfill(2) not in nacs_codes:
            continue
        try:
            lat, lng = float(it["lat"]), float(it["lng"])
        except (KeyError, ValueError, TypeError):
            continue
        sid = it.get("statId")
        s = stations.get(sid)
        if not s:
            s = stations[sid] = {
                "id": sid,
                "name": it.get("statNm", ""),
                "addr": it.get("addr", ""),
                "loc": it.get("location", ""),
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "useTime": it.get("useTime", ""),
                "busi": it.get("busiNm", ""),
                "call": it.get("busiCall", ""),
                "parkingFree": it.get("parkingFree", ""),
                "limit": it.get("limitDetail", "") if it.get("limitYn") == "Y" else "",
                "note": it.get("note", ""),
                "chargers": [],
            }
        s["chargers"].append(
            {
                "id": it.get("chgerId", ""),
                "type": str(it.get("chgerType", "")).zfill(2),
                "stat": str(it.get("stat", "")),
                "kw": it.get("output", ""),
                "upd": it.get("statUpdDt", ""),
            }
        )

    out = {
        "generatedAt": now(),
        "codes": sorted(nacs_codes),
        "stations": list(stations.values()),
    }
    with open(os.path.join(HERE, "nacs.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(s["chargers"]) for s in out["stations"])
    print(f"NACS 충전소 {len(out['stations']):,}곳 / 충전기 {n:,}대 → nacs.json 저장")
    if not out["stations"]:
        print("NACS 가 0건입니다. 위 chgerType 분포를 보고 --codes 를 조정하세요.")


if __name__ == "__main__":
    main()
