from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "봇 서버 정상 작동중!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)