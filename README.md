# 画像一括分析＆タグ付けツール

指定したフォルダ内の画像をOpenAIのGPT-4oモデルで自動分析し、「画像の説明」と「関連タグ」を生成・保存するPythonスクリプトです。

このプロジェクトには2つのバージョンのスクリプトが含まれています。
* **`prototype.py` (基本版):** 分析結果を **CSVファイル**に保存します。手軽に試したい方向けです。
* **`prototype2.py` (高機能版):** 分析結果を **CSVファイルとMySQLデータベース**の両方に保存します。データの永続的な管理や検索を行いたい方向けです。

---

## 📸 主な機能

### 全バージョン共通
-   指定フォルダ内の画像ファイル（.jpg, .jpeg, .png）を再帰的に検索
-   OpenAI GPT-4oによる画像内容の分析と説明文の生成
-   各画像に5つの関連キーワードタグを生成
-   分析結果をCSVファイルに出力

### 高機能版 (`prototype2.py`) のみ
-   分析結果をMySQLデータベースにも保存（重複データは上書き更新）
-   起動時にMySQLのテーブルを自動で作成

---

## ⚙️ セットアップ手順

### 1. 事前準備
-   Python 3.8以上
-   OpenAI APIキー
-   **高機能版のみ:** MySQLサーバー

### 2. ライブラリのインストール
目的に応じて、以下のどちらかのコマンドを実行してください。

* **基本版 (`prototype.py`) のみを利用する場合:**
    ```bash
    pip install openai python-dotenv
    ```

* **高機能版 (`prototype2.py`) を利用する場合:**
    ```bash
    pip install openai python-dotenv mysql-connector-python
    ```

### 3. `.env` ファイルの作成
スクリプトと同じ階層に `.env` ファイルを作成し、設定を記述します。

**.env.example**
```env
# --- 共通設定 (必須) ---
# ご自身のOpenAI APIキーを設定
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 分析したい画像が保存されているPC上のフォルダパスを指定
IMAGE_FOLDER_PATH="C:/Users/YourUser/Pictures/TargetFolder"

# 分析結果を保存するCSVファイルのパスと名前を指定
OUTPUT_CSV_PATH="./analysis_results.csv"


# --- 高機能版 (`prototype2.py`) のみで必要な設定 ---
MYSQL_HOST="localhost"
MYSQL_USER="your_mysql_user"
MYSQL_PASSWORD="your_mysql_password"
MYSQL_DATABASE="image_metadata_db"