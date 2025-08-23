## 반달곰 커피 홈페이지

참조링크: https://반달곰 커피

문구: 오디오 출력 소스코드

코드 블록 (Python)
```python
lang = request.args.get('lang', DEFAULT_LANG)
fp = BytesIO()
gTTS(text, "com", lang).write_to_fp(fp)
encoded_audio_data = base64.b64encode(fp.getvalue())
```
![david](https://github.com/user-attachments/assets/901aebba-e43a-4a7d-9385-5f50dad7b4e1)

