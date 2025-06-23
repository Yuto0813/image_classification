import os
import csv
import base64
import json
from openai import OpenAI
from PIL import Image
import datetime
from dotenv import load_dotenv

# ▼▼▼ ユーザー設定 ▼▼▼
# ----------------------------------------------------------------
# .envファイルから環境変数を読み込む
load_dotenv()

# 1. OpenAI APIキーの設定
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 2. 分析したい画像が入っている「PC上のフォルダパス」
IMAGE_FOLDER_PATH = os.getenv('IMAGE_FOLDER_PATH')

# 3. 分析結果を保存するCSVファイルの名前
OUTPUT_CSV_PATH = os.getenv('OUTPUT_CSV_PATH')
# ----------------------------------------------------------------
# ▲▲▲ ユーザー設定はここまで ▲▲▲


# OpenAIクライアントを初期化
try:
    client = OpenAI()
except Exception as e:
    print(f"OpenAIクライアントの初期化に失敗しました。APIキーが正しく設定されているか確認してください。エラー: {e}")
    exit()

def encode_image_to_base64(image_path):
    """画像をBase64形式にエンコードするヘルパー関数"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_images_with_openai():
    """指定されたフォルダ内の画像をOpenAI APIで分析し、説明とタグをCSVに保存する"""
    
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
                            response_format={"type": "json_object"}, # 出力をJSON形式に強制
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
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=300 # 少し長めの回答を許可
                        )
                        
                        # ★★ 変更点：AIからのJSON形式の回答を解析 ★★
                        ai_response_json = response.choices[0].message.content
                        data = json.loads(ai_response_json) # JSON文字列をPythonの辞書に変換
                        
                        description = data.get('description', '（説明なし）')
                        tags_list = data.get('tags', [])
                        
                        # リスト形式のタグを、カンマ区切りの文字列に変換して保存
                        tags_str = ", ".join(tags_list)
                        
                        # 結果をCSVに書き込む
                        writer.writerow({
                            'file_path': file_path,
                            'description': description,
                            'tags': tags_str,
                            'analyzed_at': datetime.datetime.now().isoformat()
                        })

                    except Exception as e:
                        print(f"    !! エラー発生: {file_path} の処理中にエラー。スキップします。エラー内容: {e}")

    print(f"\n処理が完了しました。結果は '{OUTPUT_CSV_PATH}' に保存されています。")


if __name__ == '__main__':
    analyze_images_with_openai()