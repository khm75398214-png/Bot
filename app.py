user_msg = req["userRequest"]["utterance"]

if user_msg == "핑":
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "퐁"}}
            ]
        }
    }

elif user_msg == "경고":
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "경고 1회"}}
            ]
        }
    }

else:
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "몰루"}}
            ]
        }
    }