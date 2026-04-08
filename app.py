from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# 🔥 Firebase 연결
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# 🔥 경고 함수
def add_warning(user_id):
    doc = db.collection("warnings").document(user_id)

    data = doc.get()

    if data.exists:
        count = data.to_dict().get("count", 0) + 1
    else:
        count = 1

    doc.set({"count": count})
    return count

@app.route('/bot', methods=['POST'])
def bot():
    data = request.json
    msg = data.get("userRequest", {}).get("utterance", "")
    user_id = data.get("userRequest", {}).get("user", {}).get("id", "")

    reply = "몰루?"

    if msg == "핑":
        reply = "퐁"

    elif msg.startswith("!경고"):
        count = add_warning(user_id)
        reply = f"경고 {count}회"

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": reply
                    }
                }
            ]
        }
    })

app.run(host='0.0.0.0', port=5000)