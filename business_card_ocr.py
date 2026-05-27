!pip install roboflow easyocr opencv-python pandas --quiet

from roboflow import Roboflow
import easyocr
import pandas as pd
import numpy as np
import re

# ==========================================================
# 設定
# ==========================================================
API_KEY = "ROBOFLOW_API_KEY"
WORKSPACE = "first-9kwz3"
PROJECT = "business-card-sg7cv"
VERSION = 1

IMAGE_PATH = "business_card.jpg"

# ==========================================================
# Roboflow UniverseのAIモデルで物体検出
# ==========================================================
rf = Roboflow(api_key=API_KEY)
model = rf.workspace(WORKSPACE).project(PROJECT).version(VERSION).model

yolo_result = model.predict(
    IMAGE_PATH,
    confidence=40,
    overlap=30
).json()

print("\n=== Object Detected ===")

# ==========================================================
# OCR
# ==========================================================
reader = easyocr.Reader(['ja', 'en'])
ocr_results = reader.readtext(IMAGE_PATH)

# ==========================================================
# 初期データ
# ==========================================================
card = {
    "会社名": "",
    "名前": "",
    "郵便番号": "",
    "住所": "",
    "電話番号": "",
    "E-mail": "",
    "URL": ""
}

# ==========================================================
# bbox + text + confidence
# ==========================================================
candidates = []

for bbox, text, conf in ocr_results:

    text = text.strip()
    if len(text) <= 1:
        continue

    x1, y1 = bbox[0]
    x2, y2 = bbox[2]

    area = abs((x2 - x1) * (y2 - y1))

    candidates.append({
        "text": text,
        "area": area,
        "conf": conf
    })

# 大きい順
candidates = sorted(candidates, key=lambda x: x["area"], reverse=True)

# ==========================================================
# 正規化関数
# ==========================================================
def clean(t):
    return t.replace(" ", "").strip()

def is_email(t):
    return "@" in t and "." in t

def is_url(t):
    t_lower = t.lower()

    if "@" in t_lower:
        return False 
    
    if any(ext in t_lower for ext in ["cojp", "co-jp", "co_jp", "com", ".jp"]):
        return True 
    
    return False 

def is_phone(t):
    return bool(re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", t))

def is_postal(t):
    return bool(re.search(r"\d{3}-\d{4}", t))

def is_company(t):
    return "株式会社" in t  or  "（株）" in t or "(株)" in t

def is_address(t):

    address_keywords = [
        "都",
        "道",
        "府",
        "県",
        "市",
        "区",
        "町",
        "村",
        "丁目"
    ]

    ng_words = [
        "登録",
        "許可",
        "認可",
        "番号",
        "旅行業者"
    ]

    return (
        any(x in t for x in address_keywords)
        and not any(x in t for x in ng_words)
    )


# ==========================================================
# 名前抽出（bbox最大）
# ==========================================================
for c in candidates:

    t = clean(c["text"])

    if (
        card["名前"] == ""
        and 2 <= len(t) <= 20
        and not any(ch.isdigit() for ch in t)
        and "株式会社" not in t
        and "@" not in t
    ):
        card["名前"] = t
        break

# ==========================================================
# その他分類（OCRベース）
# ==========================================================
for c in candidates:

    t = clean(c["text"])

    if len(t) <= 1:
        continue

    # email
    if is_email(t):
            if "cojp" in t and "co.jp" not in t:
                t = t.replace("cojp", "co.jp")
            elif "com" in t and ".com" not in t:
                t = t.replace("com", ".com")
            card["E-mail"] = t
            continue

# url
    if is_url(t):
        t_lower = t.lower()

        t = t.replace("_co-jp", ".co.jp").replace("_co_jp", ".co.jp").replace("-co-jp", ".co.jp")
        t = t.replace("_com", ".com").replace("-com", ".com")
        t = t.replace("_jp", ".jp").replace("-jp", ".jp")

        if "_co" in t: t = t.replace("_co", ".co")
        if "-co" in t: t = t.replace("-co", ".co")

        if "www" not in t.lower() and "http" not in t.lower():
            t = "www." + t

        if "www" in t.lower() and "www." not in t.lower():
            t = re.sub(r"www", "www.", t, flags=re.IGNORECASE)

        if "http" in t.lower() and "http:" not in t_lower:
            if "https" in t.lower():
                t = re.sub(r"https", "https://", t, flags=re.IGNORECASE)
            else:
                t = re.sub(r"http", "http://", t, flags=re.IGNORECASE)

        t = t.replace("://.", "://").replace("..", ".").replace("...", ".")

        card["URL"] = t
        continue

    # phone
    if is_phone(t):
        card["電話番号"] = t
        continue

    # postal
    if is_postal(t):
        t = re.sub(r"^[テ]?(\d)", r"〒\1", t)
        card["郵便番号"] = t
        continue


    # company
    if is_company(t):
        card["会社名"] = t
        continue


    # address
    if is_address(t):

        if card["住所"]:
            card["住所"] += " " + t
        else:
            card["住所"] = t

        continue

# ==========================================================
# Excel出力
# ==========================================================
df = pd.DataFrame([card])
df.to_excel("business_card_result.xlsx", index=False)

# ==========================================================
# 結果表示
# ==========================================================
print("\n================ RESULT ================")
for k, v in card.items():
    print(k, ":", v)

print("\n保存完了: business_card_result.xlsx")