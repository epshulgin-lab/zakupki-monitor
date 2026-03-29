#!/usr/bin/env python3
"""
Парсер закупок ИТС через API ГосПлан (v2.gosplan.info)
Бесплатно без регистрации до 01.07.2026
Документация: https://wiki.gosplan.info
"""

import requests
import json
import os
import time
import hashlib
from datetime import datetime

DATA_FILE = "data.json"

KEYWORDS = [
    "мониторинг ДТП и ЧС",
    "интеллектуальные транспортные системы",
    "ИТС",
    "автоматизация управления дорожным движением",
    "адаптивное управление светофорами",
    "видеоаналитика транспортных потоков",
    "управление дорожным движением",
    "детектирование транспортных средств",
    "светофорное регулирование",
    "посты мониторинга ДТП",
    "умный перекресток",
]

API_BASE = "https://v2.gosplan.info"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "updated": None, "total": 0}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_purchases(keyword, offset=0, limit=25):
    url = f"{API_BASE}/fz44/purchases/search"
    payload = {
        "text": keyword,
        "offset": offset,
        "limit": limit,
        "sort": {"field": "publishDate", "order": "desc"}
    }
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        print(f"  Таймаут для '{keyword}'")
        return None
    except Exception as e:
        print(f"  Ошибка '{keyword}': {e}")
        return None


def format_item(purchase, keyword):
    try:
        number = purchase.get("purchaseNumber") or purchase.get("number") or "—"
        name = purchase.get("purchaseObjectInfo") or purchase.get("name") or "—"
        customer = ""
        if purchase.get("customer"):
            customer = purchase["customer"].get("fullName") or purchase["customer"].get("shortName") or "—"
        date = purchase.get("publishDate") or purchase.get("createDate") or "—"
        if date and len(date) >= 10:
            try:
                dt = datetime.fromisoformat(date[:10])
                date = dt.strftime("%d.%m.%Y")
            except:
                pass
        url = f"https://zakupki.gov.ru/epz/order/notice/pricereq/view/common-info.html?regNumber={number}"
        uid = hashlib.md5(number.encode()).hexdigest()
        return {"uid": uid, "number": number, "name": name[:200], "customer": customer[:150], "date": date, "url": url, "keyword": keyword}
    except Exception as e:
        return None


def run():
    print(f"Старт: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    existing = load_existing()
    existing_uids = {item["uid"] for item in existing.get("items", [])}
    new_items = []

    for i, keyword in enumerate(KEYWORDS):
        print(f"  [{i+1}/{len(KEYWORDS)}] {keyword}")
        result = search_purchases(keyword)
        if result:
            purchases = result.get("data") or result.get("items") or result.get("results") or []
            if isinstance(result, list):
                purchases = result
            print(f"    найдено: {len(purchases)}")
            for purchase in purchases:
                item = format_item(purchase, keyword)
                if item and item["uid"] not in existing_uids:
                    existing_uids.add(item["uid"])
                    new_items.append(item)
        time.sleep(7)

    all_items = new_items + existing.get("items", [])
    all_items = all_items[:1000]
    save_data({"items": all_items, "updated": datetime.now().strftime("%d.%m.%Y %H:%M"), "total": len(all_items), "new_count": len(new_items)})
    print(f"Готово. Новых: {len(new_items)}, всего: {len(all_items)}")


if __name__ == "__main__":
    run()
