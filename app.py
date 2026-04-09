import os
import json
import datetime
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Firebase 연결
firebase_json = os.environ.get("FIREBASE_KEY")
if not firebase_json:
    raise Exception("FIREBASE_KEY 환경 변수가 없음")

cred_dict = json.loads(firebase_json)

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 설정
ALLOWED_ROOM = "영어학원 단톡", "나", "부계"
NOTICE_ROOMS = ["영어학원단톡", "나", "부계"]
MASTER_ADMINS = ["나", "부계", "가오니"]

SPAM_LIMIT = 5
SPAM_SECONDS = 3


def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_user(name):
    ref = db.collection("users").document(name)
    doc = ref.get()

    if not doc.exists:
        data = {
            "level": 1,
            "exp": 0,
            "warn": 0,
            "attendance": 0,
            "lastAttendance": "",
            "spamCount": 0,
            "spamTime": 0
        }
        ref.set(data)
        return data

    data = doc.to_dict()
    # 누락 필드 보정
    data.setdefault("level", 1)
    data.setdefault("exp", 0)
    data.setdefault("warn", 0)
    data.setdefault("attendance", 0)
    data.setdefault("lastAttendance", "")
    data.setdefault("spamCount", 0)
    data.setdefault("spamTime", 0)
    return data


def update_user(name, data):
    db.collection("users").document(name).set(data)


def is_admin(name):
    if name in MASTER_ADMINS:
        return True
    doc = db.collection("admins").document(name).get()
    return doc.exists


def add_admin(name):
    db.collection("admins").document(name).set({
        "name": name,
        "createdAt": firestore.SERVER_TIMESTAMP
    })


def remove_admin(name):
    db.collection("admins").document(name).delete()


def get_admin_list():
    result = list(MASTER_ADMINS)
    docs = db.collection("admins").stream()
    for doc in docs:
        name = doc.id
        if name not in result:
            result.append(name)
    return result


def get_banned_words():
    docs = db.collection("bannedWords").stream()
    words = []
    for doc in docs:
        words.append(doc.id)
    return words


def add_banned_word(word):
    db.collection("bannedWords").document(word).set({
        "word": word,
        "createdAt": firestore.SERVER_TIMESTAMP
    })


def remove_banned_word(word):
    db.collection("bannedWords").document(word).delete()


def save_notice(text, sender):
    db.collection("settings").document("notice").set({
        "text": text,
        "sender": sender,
        "updatedAt": firestore.SERVER_TIMESTAMP
    })


def get_notice():
    doc = db.collection("settings").document("notice").get()
    if not doc.exists:
        return None
    return doc.to_dict()


def get_ranking_text():
    users = db.collection("users").stream()
    ranking = []

    for u in users:
        d = u.to_dict()
        ranking.append((
            u.id,
            d.get("level", 1),
            d.get("exp", 0),
            d.get("attendance", 0),
            d.get("warn", 0)
        ))

    ranking.sort(key=lambda x: (-x[1], -x[2], -x[3], x[4]))

    if not ranking:
        return "🏆 랭킹\n\n데이터 없음"

    text = "🏆 랭킹 TOP 10\n\n"
    for i, r in enumerate(ranking[:10]):
        text += f"{i+1}. {r[0]} | Lv.{r[1]} | EXP {r[2]}/100 | 출석 {r[3]}회\n"
    return text.strip()


@app.route("/")
def home():
    return "ATBOT SERVER ON"


@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json(force=True)

    room = str(data.get("room", ""))
    msg = str(data.get("msg", "")).strip()
    sender = str(data.get("sender", "")).strip()

    if room != ALLOWED_ROOM:
        return jsonify({"reply": None})

    if not sender:
        return jsonify({"reply": "sender 없음"})

    user = get_user(sender)

    # 입장 메시지 흉내
    if "들어왔습니다" in msg or "환영합니다." in msg:
        return jsonify({
            "reply": f"👋 {sender}님 환영합니다!\nAT1 클랜 채팅방입니다.\n규칙을 꼭 확인해주세요."
        })

    # 관리자 목록
    if msg in ["!관리자", "!관리자목록"]:
        admins = get_admin_list()
        return jsonify({
            "reply": "👑 관리자 목록\n\n" + ("\n".join(admins) if admins else "없음")
        })

    # 관리자 등록
    if msg.startswith("!관리자등록 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!관리자등록 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !관리자등록 닉네임"})

        if is_admin(target):
            return jsonify({"reply": "이미 관리자입니다."})

        add_admin(target)
        return jsonify({"reply": f"✅ 관리자 등록 완료: {target}"})

    # 관리자 해제
    if msg.startswith("!관리자해제 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!관리자해제 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !관리자해제 닉네임"})

        if target in MASTER_ADMINS:
            return jsonify({"reply": "❌ 기본 관리자는 해제할 수 없습니다."})

        if not db.collection("admins").document(target).get().exists:
            return jsonify({"reply": "관리자가 아닙니다."})

        remove_admin(target)
        return jsonify({"reply": f"🗑 관리자 해제 완료: {target}"})

    # 공지
    if msg.startswith("!공지 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        notice = msg.replace("!공지 ", "", 1).strip()
        if not notice:
            return jsonify({"reply": "사용법: !공지 내용"})

        save_notice(notice, sender)

        return jsonify({
            "reply": f"📢 AT1 클랜 공지\n\n{notice}\n\n- 관리자: {sender}"
        })

    # 공지 확인
    if msg == "!공지확인":
        notice = get_notice()
        if not notice:
            return jsonify({"reply": "저장된 공지가 없습니다."})

        return jsonify({
            "reply": f"📢 현재 공지\n\n{notice.get('text', '')}\n\n- 관리자: {notice.get('sender', '알 수 없음')}"
        })

    # 전체공지
    if msg.startswith("!전체공지 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        notice = msg.replace("!전체공지 ", "", 1).strip()
        if not notice:
            return jsonify({"reply": "사용법: !전체공지 내용"})

        return jsonify({
            "broadcast": True,
            "rooms": NOTICE_ROOMS,
            "broadcastMessage": f"📢 전체 공지\n\n{notice}\n\n- 관리자: {sender}",
            "reply": f"✅ 전체공지 전송 준비 완료 ({len(NOTICE_ROOMS)}개 방)"
        })

    # 경고 추가
    if msg.startswith("!경고 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!경고 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !경고 닉네임"})

        target_user = get_user(target)
        target_user["warn"] += 1
        update_user(target, target_user)

        text = f"⚠️ {target} 경고 {target_user['warn']}회"
        if target_user["warn"] >= 3:
            text += "\n🚫 강퇴 요청 대상입니다."
        return jsonify({"reply": text})

    # 경고확인
    if msg.startswith("!경고확인 "):
        target = msg.replace("!경고확인 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !경고확인 닉네임"})

        target_user = get_user(target)
        return jsonify({"reply": f"📋 {target} 경고 횟수: {target_user['warn']}회"})

    # 경고초기화
    if msg.startswith("!경고초기화 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!경고초기화 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !경고초기화 닉네임"})

        target_user = get_user(target)
        target_user["warn"] = 0
        update_user(target, target_user)

        return jsonify({"reply": f"✅ {target} 경고가 초기화되었습니다."})

    # 금지어 목록
    if msg == "!금지어":
        words = get_banned_words()
        return jsonify({
            "reply": "🚫 금지어 목록\n\n" + ("\n".join(words) if words else "없음")
        })

    # 금지어 추가
    if msg.startswith("!금지어추가 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        word = msg.replace("!금지어추가 ", "", 1).strip()
        if not word:
            return jsonify({"reply": "사용법: !금지어추가 단어"})

        words = get_banned_words()
        if word in words:
            return jsonify({"reply": "이미 등록된 금지어입니다."})

        add_banned_word(word)
        return jsonify({"reply": f"✅ 금지어 추가: {word}"})

    # 금지어 삭제
    if msg.startswith("!금지어삭제 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        word = msg.replace("!금지어삭제 ", "", 1).strip()
        if not word:
            return jsonify({"reply": "사용법: !금지어삭제 단어"})

        remove_banned_word(word)
        return jsonify({"reply": f"🗑 금지어 삭제: {word}"})

    # 삭제 요청
    if msg.startswith("!삭제 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!삭제 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !삭제 닉네임"})

        return jsonify({
            "reply": f"🧹 메시지 삭제 요청\n대상: {target}\n관리자가 확인해주세요."
        })

    # 강퇴 요청
    if msg.startswith("!강퇴 "):
        if not is_admin(sender):
            return jsonify({"reply": "❌ 관리자만 사용할 수 있습니다."})

        target = msg.replace("!강퇴 ", "", 1).strip()
        if not target:
            return jsonify({"reply": "사용법: !강퇴 닉네임"})

        return jsonify({
            "reply": f"🚫 강퇴 요청\n대상: {target}\n관리자가 확인 후 강퇴해주세요."
        })

    # 레벨
    if msg == "!레벨":
        return jsonify({
            "reply":
                f"📊 {sender} 정보\n\n"
                f"레벨: {user['level']}\n"
                f"경험치: {user['exp']}/100\n"
                f"경고: {user['warn']}회\n"
                f"출석: {user['attendance']}회"
        })

    # 출석
    if msg == "!출석":
        if user["lastAttendance"] == today():
            return jsonify({"reply": "📅 오늘은 이미 출석했어."})

        user["attendance"] += 1
        user["exp"] += 20
        user["lastAttendance"] = today()

        while user["exp"] >= 100:
            user["level"] += 1
            user["exp"] -= 100

        update_user(sender, user)

        return jsonify({
            "reply":
                f"✅ 출석 완료!\n"
                f"출석 횟수: {user['attendance']}회\n"
                f"레벨: {user['level']}\n"
                f"경험치: {user['exp']}/100"
        })

    # 랭킹
    if msg == "!랭킹":
        return jsonify({"reply": get_ranking_text()})

    # 도움말
    if msg in ["!명령어", "!도움"]:
        return jsonify({
            "reply":
                "🤖 ATBOT 명령어\n\n"
                "👑 관리자\n"
                "!관리자\n"
                "!관리자등록 닉네임\n"
                "!관리자해제 닉네임\n\n"
                "📢 공지\n"
                "!공지 내용\n"
                "!공지확인\n"
                "!전체공지 내용\n\n"
                "⚠️ 경고\n"
                "!경고 닉네임\n"
                "!경고확인 닉네임\n"
                "!경고초기화 닉네임\n\n"
                "🚫 금지어\n"
                "!금지어\n"
                "!금지어추가 단어\n"
                "!금지어삭제 단어\n\n"
                "📊 정보\n"
                "!레벨\n"
                "!출석\n"
                "!랭킹\n\n"
                "🧹 관리\n"
                "!삭제 닉네임\n"
                "!강퇴 닉네임\n\n"
                "ℹ️ 기타\n"
                "!명령어 / !도움"
        })

    # 금지어 자동 감지
    banned_words = get_banned_words()
    for word in banned_words:
        if word and word in msg:
            user["warn"] += 1
            update_user(sender, user)

            text = (
                f"🚫 금지어 감지\n"
                f"대상: {sender}\n"
                f"경고: {user['warn']}회"
            )
            if user["warn"] >= 3:
                text += "\n🚫 강퇴 요청 대상입니다."
            return jsonify({"reply": text})

    # 도배 감지
    now_ts = int(datetime.datetime.now().timestamp())
    if now_ts - int(user.get("spamTime", 0)) <= SPAM_SECONDS:
        user["spamCount"] += 1
    else:
        user["spamCount"] = 1

    user["spamTime"] = now_ts

    if user["spamCount"] >= SPAM_LIMIT:
        user["warn"] += 1
        user["spamCount"] = 0
        update_user(sender, user)

        text = (
            f"🚨 도배 감지\n"
            f"대상: {sender}\n"
            f"경고: {user['warn']}회"
        )
        if user["warn"] >= 3:
            text += "\n🚫 강퇴 요청 대상입니다."
        return jsonify({"reply": text})

    # 일반 채팅 경험치
    if not msg.startswith("!"):
        user["exp"] += 5
        level_up = False

        while user["exp"] >= 100:
            user["level"] += 1
            user["exp"] -= 100
            level_up = True

        update_user(sender, user)

        if level_up:
            return jsonify({"reply": f"🎉 {sender} 레벨업! Lv.{user['level']}"})
        return jsonify({"reply": None})

    update_user(sender, user)
    return jsonify({"reply": None})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)