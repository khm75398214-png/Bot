from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/bot', methods=['POST'])
def bot():
    data = request.json
    msg = data.get("userRequest", {}).get("utterance", "")

    if msg == "핑":
        reply = "퐁"
    else:
        reply = "몰루?"

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