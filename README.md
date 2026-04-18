# Workplace Hub Tokyo 料金シミュレーター

仮設のコワーキングスペース「Workplace Hub Tokyo」を題材にした、
Python + Streamlit による料金計算アプリのサンプルプロジェクトです。

> **注記**: 本プロジェクトは個人の学習・ポートフォリオ目的で作成された架空のアプリです。
> 実在する施設とは関係ありません。全てのデータは架空の設定です。

## 機能

- 部屋の利用料金計算（時間課金・日額パック選択可）
- 備品・オプションの追加（機材/飲食/ネット）
- 利用時間による自動割引（3時間以上10%、6時間以上20%）
- 会員種別による追加割引（月額会員20%、法人契約30%）
- 明細付きの見積もり表示

## 技術スタック

- Python 3.11+
- Streamlit
- pandas
- jpholiday

## セットアップ

```bash
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで http://localhost:8501 が自動で開きます。

## ディレクトリ構成

- `app.py` - Streamlit UI
- `calculator.py` - 料金計算ロジック
- `data/` - マスタデータ（CSV）
  - `rooms.csv` - 部屋マスタ
  - `options.csv` - 備品・オプションマスタ
  - `discount_rules.csv` - 割引ルール

## データ拡張

`data/` 配下のCSVを編集することで、部屋や料金・オプションを柔軟に変更できます。

## ライセンス

MIT License
