import os
import base64
from io import BytesIO

from flask import Flask, request, render_template, url_for
from gtts import gTTS
from gtts.tts import gTTSError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ko")
LANGS = {"ko": "한국어", "en": "영어", "ja": "일본어", "es": "스페인어"}

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    audio_b64 = None
    selected_lang = DEFAULT_LANG
    input_text = ""

    if request.method == "POST":
        input_text = (request.form.get("input_text") or "").strip()
        selected_lang = request.form.get("lang", DEFAULT_LANG)

        if not input_text:
            error = "텍스트를 입력하세요."
        elif selected_lang not in LANGS:
            error = "지원하지 않는 언어입니다."
        else:
            try:
                fp = BytesIO()
                tts = gTTS(text=input_text, lang=selected_lang, tld="com")
                tts.write_to_fp(fp)
                fp.seek(0)
                audio_b64 = base64.b64encode(fp.read()).decode("ascii")
            except gTTSError as e:
                error = f"TTS 변환에 실패했습니다: {e}"
            except Exception as e:
                error = f"예상치 못한 오류: {e}"

    david_img_url = url_for("static", filename="david.jpg")

    return render_template(
        "index.html",
        error=error,
        audio=audio_b64,
        langs=LANGS,
        selected_lang=selected_lang,
        input_text=input_text,
        david_img_url=david_img_url,
    )

@app.route("/menu")
def show_menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run("0.0.0.0", 1234, debug=True)
