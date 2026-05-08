import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone, timedelta

# 取得対象のJANコード（必要に応じて追加・変更してください）
TARGET_JANS = [
    "4902370553024",   # Nintendo Switch 2 例
    "4521329432786",
    "4521329431932",
    # ここに追加したいJANを増やせます
]

def get_jst_now():
    """日本時間で現在時刻を取得"""
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).isoformat()

def fetch_item_from_1chome(jan: str):
    """買取一丁目からJANで商品情報を取得"""
    url = "https://www.1-chome.com/searchResult"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }

    try:
        # JANコードで検索
        params = {"query": jan}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 実際のサイト構造に合わせて調整（現在は簡易版）
        # 商品名を取得
        name_elem = soup.select_one(".commodity-content .title, .commodity-content .clamped-text")
        name = name_elem.get_text(strip=True) if name_elem else "商品名不明"

        # 価格を取得（複数状態がある場合は最初のものを優先）
        price_elem = soup.select_one(".commodity-text-color span, .el-radio__label .text-right")
        price_text = price_elem.get_text(strip=True) if price_elem else "要確認"
        
        # 数値だけ抽出（簡易）
        import re
        price_match = re.search(r"[\d,]+", price_text)
        price = int(price_match.group().replace(",", "")) if price_match else 0

        return {
            "jan": jan,
            "name": name[:120],
            "price": price,
            "priceText": price_text,
            "source": "買取一丁目",
            "url": f"https://www.1-chome.com/searchResult?query={jan}",
            "fetchedAt": get_jst_now()
        }

    except Exception as e:
        print(f"[ERROR] JAN {jan} の取得に失敗: {e}")
        return None

def main():
    print("=== 買取一丁目 価格更新開始 ===")
    
    updated_items = []
    
    for jan in TARGET_JANS:
        print(f"Fetching JAN: {jan} ...")
        item = fetch_item_from_1chome(jan)
        if item:
            updated_items.append(item)
    
    # data/prices.json のパス
    output_dir = "data"
    output_path = os.path.join(output_dir, "prices.json")
    os.makedirs(output_dir, exist_ok=True)
    
    # 既存データとマージ（JANで上書き）
    existing_data = []
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    
    existing_dict = {item["jan"]: item for item in existing_data}
    
    for item in updated_items:
        existing_dict[item["jan"]] = item
    
    final_data = list(existing_dict.values())
    
    # 保存
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 更新完了: {len(final_data)} 件の商品を data/prices.json に保存しました")
    print("=== 処理終了 ===")

if __name__ == "__main__":
    main()
