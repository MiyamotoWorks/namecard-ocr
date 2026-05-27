# Business Card OCR

EasyOCR + Roboflow を利用した名刺OCR自動分類システムです。

## 機能

- 名刺画像からOCRを用いてテキスト抽出
- Roboflow Universe のAIモデルで物体検出
- 名前をbboxサイズから推定
- 電話番号 / メール / URL / 住所を自動分類
- Excel出力

## 使用モデル

Roboflow Universe:  
<https://universe.roboflow.com/first-9kwz3/business-card-sg7cv>

## 使用技術

- Python
- EasyOCR
- Roboflow
- pandas
- numpy
- re

## 実行方法

```bash
python business_card_ocr.py
```

## 工夫点

OCR誤認識を考慮し、電話番号・郵便番号・URLなどは正規表現による自動補正を実装しています。