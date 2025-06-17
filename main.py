import requests
import asyncio
import edge_tts
import os
import subprocess
import speech_recognition as sr
import pandas as pd
import yfinance as yf
from difflib import get_close_matches
from requests_toolbelt.multipart.encoder import MultipartEncoder
import re
import shutil

USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
DOWNLOAD_PATH = "1/0/2"  # שלוחת ההקלטות החדשה
UPLOAD_PATH = "ivr2:/1/0/22/001.wav"  # שלוחת ההעלאה החדשה

async def main_loop():
    stock_dict = load_stock_list("hebrew_stocks.csv")
    print("🔁 בלולאת בדיקה מתחילה...")

    ensure_ffmpeg()
    last_processed_file = None

    while True:
        filename, file_name_only = download_yemot_file()

        if not file_name_only:
            await asyncio.sleep(1)
            continue

        if file_name_only == last_processed_file:
            await asyncio.sleep(1)
            continue

        last_processed_file = file_name_only
        print(f"📥 קובץ חדש לזיהוי: {file_name_only}")

        if filename:
            recognized = transcribe_audio(filename)
            if recognized:
                best_match = get_best_match(recognized, stock_dict)
                if best_match:
                    stock_info = stock_dict[best_match]
                    data = get_stock_data(stock_info['ticker'])
                    if data:
                        text = format_text(stock_info, data)
                        print(f"🟩 זוהה {best_match} → מעלה לימות: {stock_info['display_name']}")
                    else:
                        text = f"לא נמצאו נתונים עבור {stock_info['display_name']}"
                else:
                    text = "לא זוהה נייר ערך תואם"
            else:
                text = "לא זוהה דיבור ברור"

            await create_audio(text, "output.mp3")
            convert_mp3_to_wav("output.mp3", "output.wav")
            upload_to_yemot("output.wav")
            delete_yemot_file(file_name_only)
            print("✅ הושלמה פעולה מחזורית\n")

        await asyncio.sleep(1)

# ... (שאר הפונקציות נשארות זהות) ...

def upload_to_yemot(wav_file):
    url = "https://www.call2all.co.il/ym/api/UploadFile"
    m = MultipartEncoder(
        fields={
            "token": TOKEN,
            "path": UPLOAD_PATH,
            "upload": (wav_file, open(wav_file, 'rb'), 'audio/wav')
        }
    )
    response = requests.post(url, data=m, headers={'Content-Type': m.content_type})
    print(f"⬆️ קובץ עלה לשלוחה {UPLOAD_PATH}")

if __name__ == "__main__":
    asyncio.run(main_loop())
