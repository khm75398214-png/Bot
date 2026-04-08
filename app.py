from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Firebase 연결
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)  # 🔥 이걸로 수정

    if not data:
        return "No data"

    user_msg = data["userRequest"]["utterance"]

    # 명령어 처리
    if user_msg == "핑":
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "퐁"}}]
            }
        }

    elif user_msg.startswith("!경고"):
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "경고 1회"}}]
            }
        }

    # 기본 응답
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": "몰루"}}]
        }
    }

app.run(host="0.0.0.0", port=5000)