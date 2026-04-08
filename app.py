from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "server is running"

@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)
    msg = data.get("userRequest", {}).get("utterance", "")

    if msg == "핑":
        reply = "퐁"
    elif msg == "경고" or msg.startswith("!경고"):
        reply = "경고 1회"
    else:
        reply = "몰루"

    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": reply}}
            ]
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
