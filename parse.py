#!/usr/bin/env python3
import urllib.request, urllib.parse, json, os, time, hashlib
from datetime import datetime, timedelta

DATA_FILE = "data.json"
DAYS_BACK = 60

KEYWORDS = [
    "мониторинг ДТП и ЧС",
    "интеллектуальная транспортная система",
    "адаптивное управление светофорами",
    "автоматизация управления дорожным движением",
    "видеоаналитика транспортных потоков",
    "детектирование транспортных средств",
    "светофорное регулирование",
    "посты мониторинга ДТП",
    "умный перекресток",
    "система управления дорожным движением",
    "транспортный детектор",
    "дорожный контроллер",
    "АСУДД",
    "ИТС агломерация",
]

ORGS = {
    "7710350884": "ГКУ ЦОДД Москва",
    "7708305010": "Минтранс Москвы",
    "5024066047": "ЦОДД Московская обл",
    "7801145804": "ДОДД Санкт-Петербург",
    "7830001886": "Минтранс СПб",
    "2309179043": "ЦОДД Краснодарский край",
    "6164086571": "ЦОДД Ростовская обл",
    "3444047949": "ЦОДД Волгоград",
    "2635116133": "ЦОДД Ставропольский край",
    "1655296696": "ЦОДД Казань",
    "0278116632": "ЦОДД Уфа",
    "5902196839": "ЦОДД Пермь",
    "5260345359": "ЦОДД Нижний Новгород",
    "6453074976": "ЦОДД Саратов",
    "6316008913": "ЦОДД Самара",
    "1831090505": "ЦОДД Ижевск",
    "5612048090": "ЦОДД Оренбург",
    "1650278987": "ЦОДД Набережные Челны",
    "1326201859": "ЦОДД Саранск",
    "2130221237": "ЦОБДД Чебоксары",
    "1215189670": "ЦОДД Йошкар-Ола",
    "1832128011": "Минтранс Удмуртия",
    "6670233762": "ЦОДД Екатеринбург",
    "7204212527": "ЦОДД Тюмень",
    "7453003963": "ЦОДД Челябинск",
    "8601060879": "ЦОДД Ханты-Мансийск",
    "8904068914": "ЦОДД Салехард",
    "5402570056": "ГКУ НСО ЦОДД Новосибирск",
    "5407070339": "ГЦОДД Новосибирск",
    "2466057404": "ЦОДД Красноярск",
    "5503089620": "ЦОДД Омск",
    "4205316607": "ЦОДД Кемерово",
    "7017323262": "ЦОДД Томск",
    "3849000994": "ЦОДД Иркутск",
    "0323118680": "ЦОДД Улан-Удэ",
    "2721207145": "ЦОДД Хабаровск",
    "2540208890": "ЦОДД Владивосток",
    "1435322037": "ЦОДД Якутск",
    "2901199534": "ЦОДД Архангельск",
    "1001286830": "ЦОДД Петрозаводск",
    "5321107668": "ЦОДД Великий Новгород",
    "6027108872": "ЦОДД Псков",
    "6950073860": "ЦОДД Тверь",
    "3525193390": "ЦОДД Вологда",
    "3663048147": "ЦОДД Воронеж",
    "6829042927": "ЦОДД Тамбов",
    "6234139120": "ЦОДД Рязань",
    "7105501300": "ЦОДД Тула",
    "3702733484": "ЦОДД Иваново",
    "7602087270": "ЦОДД Ярославль",
    "4401099500": "ЦОДД Кострома",
    "3254504751": "ЦОДД Брянск",
    "6732115800": "ЦОДД Смоленск",
    "5702045840": "ЦОДД Орёл",
    "4826063890": "ЦОДД Липецк",
    "3123404890": "ЦОДД Белгород",
    "7728516789": "Минтранс МО",
}

API_BASE = "https://v2.gosplan.info"
DATE_FROM = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"items": [], "updated": None, "total": 0}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def fetch(params_dict):
    params_dict["date_from"] = DATE_FROM
    params = urllib.parse.urlencode(params_dict)
    url = f"{API_BASE}/fz44/purchases?{params}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  Ошибка: {e}"); return None

def format_item(p, keyword):
    try:
        number = p.get("purchase_number") or "—"
        name = p.get("object_info") or "—"
        customers = p.get("customers") or p.get("owners") or []
        customer = customers[0] if customers else "—"
        date = p.get("published_at") or "—"
        if date and len(date) >= 10:
            try: date = datetime.fromisoformat(date[:10]).strftime("%d.%m.%Y")
            except: pass
        return {
            "uid": hashlib.md5(number.encode()).hexdigest(),
            "number": number, "name": str(name)[:200],
            "customer": str(customer)[:150], "date": date,
            "url": f"https://zakupki.gov.ru/epz/order/notice/pricereq/view/common-info.html?regNumber={number}",
            "keyword": keyword
        }
    except: return None

def run():
    print(f"Старт: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Период: с {DATE_FROM} по сегодня")
    existing = load_existing()
    existing_uids = {item["uid"] for item in existing.get("items", [])}
    new_items = []

    print(f"\n--- Ключевые слова ({len(KEYWORDS)}) ---")
    for i, keyword in enumerate(KEYWORDS):
        print(f"  [{i+1}/{len(KEYWORDS)}] {keyword}")
        data = fetch({"limit": 25, "skip": 0, "name": keyword})
        if data:
            purchases = data if isinstance(data, list) else []
            if purchases: print(f"    найдено: {len(purchases)}")
            for p in purchases:
                item = format_item(p, keyword)
                if item and item["uid"] not in existing_uids:
                    existing_uids.add(item["uid"]); new_items.append(item)
        time.sleep(3)

    print(f"\n--- ЦОДД и Минтрансы ({len(ORGS)}) ---")
    for inn, name in ORGS.items():
        print(f"  {name}")
        data = fetch({"limit": 25, "skip": 0, "customer": inn})
        if data:
            purchases = data if isinstance(data, list) else []
            if purchases: print(f"    найдено: {len(purchases)}")
            for p in purchases:
                item = format_item(p, name)
                if item and item["uid"] not in existing_uids:
                    existing_uids.add(item["uid"]); new_items.append(item)
        time.sleep(3)

    all_items = (new_items + existing.get("items", []))[:2000]
    save_data({"items": all_items, "updated": datetime.now().strftime("%d.%m.%Y %H:%M"), "total": len(all_items), "new_count": len(new_items)})
    print(f"\nГотово. Новых: {len(new_items)}, всего: {len(all_items)}")

if __name__ == "__main__": run()
