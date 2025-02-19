from flask import Flask, render_template, jsonify
import sqlite3, random, json
from datetime import datetime, timedelta
import google.generativeai as genai
import os

# 設定 Gemini API 金鑰 (此處僅示範，請勿在公開環境留明碼)
genai.configure(api_key='AIzaSyB...')

app = Flask(__name__)
DATABASE = 'analyze.db'

# ====== 歌曲資料庫相關程式碼 ======
def random_date(start, end):
    """在兩個 datetime 物件間產生一個隨機的 datetime"""
    delta = end - start
    int_delta = delta.days * 24 * 60 * 60 + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def init_song_db():
    """建立 songs 資料表 (若尚未存在)"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_name TEXT,
            upload_time TEXT,
            fame_indicator TEXT,
            trending_days INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def populate_song_db():
    """若 songs 資料表為空，則隨機產生 10 筆資料"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM songs")
    count = c.fetchone()[0]
    if count == 0:
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()
        for i in range(1, 11):
            song_name = f"Song {i}"
            random_dt = random_date(start_date, end_date).isoformat()
            fame_indicator = random.choice(["會紅喔!", "不紅喔QQ"])
            trending_days = random.randint(1, 29)  # 數值約束在 30 天以下
            c.execute('''
                INSERT INTO songs (song_name, upload_time, fame_indicator, trending_days)
                VALUES (?, ?, ?, ?)
            ''', (song_name, random_dt, fame_indicator, trending_days))
    conn.commit()
    conn.close()

def get_latest_song():
    """撈取上傳時間最新的歌曲資料"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM songs ORDER BY upload_time DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

# 初始化歌曲資料庫
init_song_db()
populate_song_db()

# ====== analysis 資料庫相關程式碼 ======
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            gender_json TEXT,
            country_json TEXT,
            age_json TEXT,
            scenario_text TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_percentages(n, base_mean, std_dev):
    """通用隨機分配函式。"""
    values = []
    for _ in range(n):
        val = max(random.gauss(base_mean, std_dev), 1)
        values.append(val)
    total = sum(values)
    return [round((v / total) * 100, 2) for v in values]

def generate_gender_data():
    """將「男 + 女」合計控制在 90~99%，其餘給「其他」"""
    total_mf = random.uniform(90, 99)
    male = random.uniform(0, total_mf)
    female = total_mf - male
    other = 100 - total_mf
    return {
        "categories": ["男", "女", "其他"],
        "percentages": [round(male, 2), round(female, 2), round(other, 2)]
    }

def generate_country_data():
    """隨機選擇 5 國 + 1「其他」，並用亂數分配比例"""
    countries = ["USA", "UK", "Canada", "Germany", "France",
                 "Australia", "Brazil", "Japan", "South Korea", "India"]
    selected = random.sample(countries, 5)
    values = [random.uniform(1, 10) for _ in range(6)]
    total = sum(values)
    percentages = [round((v / total) * 100, 2) for v in values]
    return {
        "categories": selected + ["其他"],
        "percentages": percentages
    }

def generate_scenario_text():
    """呼叫 Gemini API 分析音訊，生成描述文字 (若失敗則回傳錯誤訊息)"""
    try:
        your_file = genai.upload_file(path='music/200.Machine Gun Kelly - Wild Boy Official.wav')
        prompt = (
            "生成可以表達音樂適用情境的描述文字..."
        )
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(contents=[prompt, your_file])
        return response.text
    except Exception as e:
        return "音訊分析失敗：" + str(e)

def generate_age_data():
    categories = ["12歲以下", "13-17歲", "18-24歲", "25-34歲", "35-44歲", "45-54歲", "55-64歲", "65歲以上"]
    return {
        "categories": categories,
        "percentages": generate_percentages(8, 12.5, 2)
    }

def generate_random_data():
    """整合所有平台資料 (含 TIDAL 與 Amazon Music)"""
    platforms = ["youtube", "spotify", "apple-music", "tidal", "amazon-music"]
    scenario = generate_scenario_text()
    data = {}
    for p in platforms:
        data[p] = {
            "gender": generate_gender_data(),
            "country": generate_country_data(),
            "age": generate_age_data(),
            "scenario": scenario
        }
    return data

def store_data_in_db(data):
    """將平台資料寫入 analysis 資料表"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    for platform, details in data.items():
        c.execute('''
            INSERT INTO analysis (platform, gender_json, country_json, age_json, scenario_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            platform,
            json.dumps(details["gender"], ensure_ascii=False),
            json.dumps(details["country"], ensure_ascii=False),
            json.dumps(details["age"], ensure_ascii=False),
            details["scenario"],
            created_at
        ))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    # 產生並儲存隨機數據
    data = generate_random_data()
    store_data_in_db(data)

    # 撈取最新歌曲資料
    latest_song = get_latest_song()

    # 將 data 轉為 JSON 字串
    data_str = json.dumps(data, ensure_ascii=False)
    # 不需要再手動替換 \n,\r，直接在模板用 tojson 避免跳脫問題

    return render_template(
        "BD3.html",
        data_str=data_str,
        myname="My name is PP!",
        latest_song=latest_song
    )

@app.route("/data")
def get_data():
    data = generate_random_data()
    store_data_in_db(data)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
