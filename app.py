from flask import Flask, request, jsonify

app = Flask(__name__)

# 관리자 목록 (여기에 닉네임 추가)
admins = ["가오니"]

# 경고 데이터 (임시 저장 - 서버 꺼지면 초기화됨)
warnings = {}

# 특정 방에서만 작동
allowed_rooms = ["홍보방"]

@app.route("/", methods=["POST"])
def kakao():
    req = request.get_json()
    
    user_msg = req["userRequest"]["utterance"]
    user = req["userRequest"]["user"]["id"]
    room = req["userRequest"]["channel"]["name"]

    # 🚪 특정 방 제한
    if room not in allowed_rooms:
        return response("이 방에서는 사용 불가")

    # 🏓 핑 테스트
    if user_msg == "핑":
        return response("퐁")

    # ⚠️ 경고 시스템
    elif user_msg.startswith("경고"):
        if user not in warnings:
            warnings[user] = 0
        
        warnings[user] += 1
        return response(f"경고 {warnings[user]}회")

    # 👑 관리자 등록
    elif user_msg.startswith("관리자등록"):
        if user_msg.split(" ")[1] in admins:
            return response("이미 관리자임")
        
        admins.append(user_msg.split(" ")[1])
        return response("관리자 등록 완료")

    # ❌ 관리자 해제
    elif user_msg.startswith("관리자해제"):
        target = user_msg.split(" ")[1]
        
        if target in admins:
            admins.remove(target)
            return response("관리자 해제 완료")
        else:
            return response("관리자 아님")

    # 📢 공지
    elif user_msg.startswith("공지"):
        if user not in admins:
            return response("관리자만 가능")
        
        msg = user_msg.replace("공지 ", "")
        return response(f"[공지]\n{msg}")

    # 🔚 기본 응답
    else:
        return response("몰루")

# 응답 함수 (중요)
def response(text):
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ]
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)