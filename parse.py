#!/usr/bin/env python3
"""
Парсер zakupki.gov.ru — запускается GitHub Actions, сохраняет data.json
"""

import requests
import json
import os
import time
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup

KEYWORDS = [
    "мониторинг ДТП и ЧС",
    "интеллектуальные транспортные системы",
    "ИТС светофор",
    "автоматизация управления дорожным движением",
    "адаптивное управление светофорами",
    "видеоаналитика транспортных потоков",
    "управление дорожным движением",
    "детектирование транспортных средств",
    "светофорное регулирование",
    "посты мониторинга ДТП",
    "умный перекресток",
]

BASE_URL = "https://zakupki.gov.ru/epz/pricereq/search/results.html"
DATA_FILE = "data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "updated": None}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def search_keyword(keyword):
    params = {
        "searchString": keyword,
        "morphology": "on",
        "search-filter": "Дате размещения",
        "published": "on",
        "proposed": "on",
        "ended": "on",
        "sortBy": "UPDATE_DATE",
        "pageNumber": 1,
        "sortDirection": "false",
        "recordsPerPage": "_25",
        "showLotsInfoHidden": "false",
    }
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
            r.raise_for_status()
            return r.text
        except requests.exceptions.Timeout:
            print(f"  ⏱  Таймаут попытка {attempt+1}/3 для '{keyword}'")
            time.sleep(3)
        except Exception as e:
            print(f"  ⚠️  Ошибка запроса '{keyword}': {e}")
            return None
    print(f"  ✗ Пропускаем '{keyword}' — все попытки исчерпаны")
    return None


def parse_results(html, keyword):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    cards = soup.select("div.search-registry-entry-block")

    for card in cards:
        try:
            link_tag = card.select_one("a.registry-entry__header-mid__number")
            if not link_tag:
                continue
            number = link_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            url = f"https://zakupki.gov.ru{href}" if href.startswith("/") else href

            body_vals = card.select("div.registry-entry__body-value")
            name = body_vals[0].get_text(strip=True) if body_vals else "—"
            customer = body_vals[1].get_text(strip=True) if len(body_vals) > 1 else "—"

            date_tag = card.select_one("div.data-block__value")
            date = date_tag.get_text(strip=True) if date_tag else "—"

            uid = hashlib.md5(number.encode()).hexdigest()

            items.append({
                "uid": uid,
                "number": number,
                "name": name,
                "customer": customer,
                "date": date,
                "url": url,
                "keyword": keyword,
            })
        except Exception:
            continue

    return items


def run():
    print(f"🚀 Старт парсера: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    existing = load_existing()
    existing_uids = {item["uid"] for item in existing.get("items", [])}
    new_items = []

    for i, keyword in enumerate(KEYWORDS):
        print(f"  [{i+1}/{len(KEYWORDS)}] «{keyword}»")
        html = search_keyword(keyword)
        if html:
            items = parse_results(html, keyword)
            print(f"    → найдено карточек: {len(items)}")
            for item in items:
                if item["uid"] not in existing_uids:
                    existing_uids.add(item["uid"])
                    new_items.append(item)
        time.sleep(2)

    all_items = new_items + existing.get("items", [])
    all_items = all_items[:1000]  # храним последние 1000

    result = {
        "items": all_items,
        "updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "total": len(all_items),
        "new_count": len(new_items),
    }

    save_data(result)
    print(f"✅ Готово. Новых: {len(new_items)}, всего: {len(all_items)}")


if __name__ == "__main__":
    run()
