import requests as req
import sys
import time
import json

clientId = str(sys.argv[1]).strip()
file_path = 'token.txt'

def read_token():
    with open(file_path, 'r') as file:
        return file.read().strip()

def normalize_turkish_characters(text):
    replacements = {
        "Ç": "C", "Ö": "O", "İ": "I", "Ğ": "G", "Ü": "U", "ı": "i",
        "ç": "c", "ö": "o", "ğ": "g", "ü": "u", "ş": "s", "Ş": "S"
    }
    for turkish_char, english_char in replacements.items():
        text = text.replace(turkish_char, english_char)
    return text

def normalize_value(value):
    if isinstance(value, str):
        return normalize_turkish_characters(value)
    elif isinstance(value, dict):
        return {k: normalize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [normalize_value(item) for item in value]
    else:
        return value

def get_friend_feed(max_total_attempts=3):
    token = read_token()
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    FUNCTION_TIMEOUT = 15
    VERIFY_SSL = True
    MAX_RETRIES = 5
    RETRY_DELAY = 0.25

    friendsHeaders = {
        "Authorization": f"Bearer {token}",
        "Client-Id": clientId,
        "User-Agent": ua,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        friendListResp = req.get(
            "https://guc-spclient.spotify.com/presence-view/v1/buddylist",
            headers=friendsHeaders,
            timeout=FUNCTION_TIMEOUT,
            verify=VERIFY_SSL,
        )

        if friendListResp.status_code == 200:
            try:
                friends_data = friendListResp.json()
                normalized_data = [
                    {key: normalize_value(value) for key, value in friend.items()}
                    for friend in friends_data.get("friends", [])
                ]
                print(json.dumps(normalized_data, ensure_ascii=False, indent=2))
                sys.stdout.flush()
                return  # Success: exit the function.
            except ValueError:
                print("Error: Invalid JSON response")
                sys.stdout.flush()
                sys.exit("Terminating: Invalid JSON response")
        elif friendListResp.status_code == 401:
            # Likely token expired, wait and retry.
            time.sleep(RETRY_DELAY)
        else:
            break
    else:
        # If we reach here, MAX_RETRIES were exhausted.
        # Now check if we've already attempted token refresh.
        if max_total_attempts > 1:
            # Pull the updated token from the file and try again.
            token = read_token()
            sys.stdout.flush()
            get_friend_feed(max_total_attempts - 1)
        else:
            # We've already refreshed the token once; now stop the script.
            sys.exit("Terminating: Failed to fetch friend feed after token refresh.")

# Start the process:
get_friend_feed()
