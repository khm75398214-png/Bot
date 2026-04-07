from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def kakao():
    data = request.get_json()
    
    user_msg = data['userRequest']['utterance']

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"너가 보낸 말: {user_msg}"
                    }
                }
            ]
        }
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
