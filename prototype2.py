import os
import csv
import base64
import json
import mysql.connector # ### 変更 ###: sqlite3からmysql.connectorに変更
from mysql.connector import Error # ### 追加 ###: MySQLのエラーを扱うためにインポート
import datetime
from openai import OpenAI
from dotenv import load_dotenv

# ▼▼▼ ユーザー設定 ▼▼▼
# ----------------------------------------------------------------
load_dotenv()

# 1. OpenAI APIキーの設定
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 2. 分析したい画像が入っている「PC上のフォルダパス」
IMAGE_FOLDER_PATH = os.getenv('IMAGE_FOLDER_PATH')

# 3. 分析結果を保存するCSVファイルの名前
OUTPUT_CSV_PATH = os.getenv('OUTPUT_CSV_PATH')

# ### 変更 ###: 4. MySQLの接続情報を.envファイルから読み込む
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}
# ----------------------------------------------------------------
# ▲▲▲ ユーザー設定はここまで ▲▲▲


# OpenAIクライアントを初期化 (変更なし)
try:
    client = OpenAI()
except Exception as e:
    print(f"OpenAIクライアントの初期化に失敗しました。エラー: {e}")
    exit()

### 変更 ###: setup_database関数をMySQL用に書き換え
def setup_database():
    """MySQLデータベースにテーブルを初期化する関数"""
    print(f"データベース '{db_config['database']}' を準備しています...")
    try:
        # MySQLに接続
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # metadataテーブルを作成（もし存在していなければ）
        # 文字化け対策として、文字コードにutf8mb4を指定
        # ファイルパスが長くなる可能性を考慮し、VARCHAR(512)に設定
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            file_path VARCHAR(512) PRIMARY KEY,
            description TEXT,
            tags TEXT,
            analyzed_at VARCHAR(50)
        ) DEFAULT CHARSET=utf8mb4
        ''')
        conn.commit()
        print("データベースのテーブル準備が完了しました。")

    except Error as e:
        print(f"データベースのセットアップ中にエラーが発生しました: {e}")
    finally:
        # 接続を閉じる
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

### 変更 ###: save_to_database関数をMySQL用に書き換え
def save_to_database(data_dict):
    """分析結果をMySQLデータベースに保存する関数"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # REPLACE INTOを使い、同じfile_pathのデータがあれば上書き、なければ新規追加
        # プレースホルダが ? から %s に変わる点に注意
        sql = '''
        REPLACE INTO metadata (file_path, description, tags, analyzed_at)
        VALUES (%s, %s, %s, %s)
        '''
        values = (
            data_dict['file_path'],
            data_dict['description'],
            data_dict['tags'],
            data_dict['analyzed_at']
        )
        cursor.execute(sql, values)
        conn.commit()

    except Error as e:
        print(f"  !! データベースへの保存中にエラーが発生しました: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# encode_image_to_base64関数 (変更なし)
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# analyze_images_with_openai関数 (データベース関数の呼び出し部分以外は変更なし)
def analyze_images_with_openai():
    with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['file_path', 'description', 'tags', 'analyzed_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        print(f"フォルダ '{IMAGE_FOLDER_PATH}' のスキャンを開始します...")

        for root, _, files in os.walk(IMAGE_FOLDER_PATH):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(root, filename)

                    try:
                        print(f"  - 分析中: {file_path}")
                        
                        base64_image = encode_image_to_base64(file_path)
                        
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            response_format={"type": "json_object"},
                            messages=[
                                {
                                    "role": "system",
                                    "content": """あなたは優秀な画像分析エキスパートです。ユーザーが送信した画像を分析し、以下の仕様のJSONオブジェクト形式で、それのみを回答してください。
- "description"キー: 画像の内容を詳細に、かつ自然な日本語の文章で説明します。
- "tags"キー: 画像に関連するキーワードを、日本語の文字列の配列（リスト）として5つ記述します。
例: {"description": "夕焼けのビーチで犬がボールを追いかけている。", "tags": ["犬", "ビーチ", "夕焼け", "ボール", "海"]}
余計な説明や前置きは一切不要です。"""
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                    ]
                                }
                            ],
                            max_tokens=300
                        )
                        
                        ai_response_json = response.choices[0].message.content
                        data = json.loads(ai_response_json)
                        
                        description = data.get('description', '（説明なし）')
                        tags_list = data.get('tags', [])
                        tags_str = ", ".join(tags_list)
                        
                        result_data = {
                            'file_path': file_path,
                            'description': description,
                            'tags': tags_str,
                            'analyzed_at': datetime.datetime.now().isoformat()
                        }
                        
                        # 1. 結果をCSVに書き込む
                        writer.writerow(result_data)
                        
                        # 2. 結果をデータベースに保存 (呼び出し部分は変更なし)
                        save_to_database(result_data)

                    except Exception as e:
                        print(f"    !! エラー発生: {file_path} の処理中にエラー。スキップします。エラー内容: {e}")

    print(f"\n処理が完了しました。")
    print(f"  - CSVファイル: '{OUTPUT_CSV_PATH}'")
    print(f"  - MySQLデータベース: '{db_config['database']}' の 'metadata' テーブル")

# メインの実行部分
if __name__ == '__main__':
    # 最初にデータベースを準備する (呼び出し部分は変更なし)
    setup_database()
    analyze_images_with_openai()