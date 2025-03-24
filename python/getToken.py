import base64
import platform
import pyotp
import requests as req
import signal
from time import time_ns
from requests.exceptions import Timeout as TimeoutException
import sys
import time

SP_DC = str(sys.argv[1])
SERVER_TIME_URL = "https://open.spotify.com/server-time"
FUNCTION_TIMEOUT = 15
VERIFY_SSL = True

def timeout_handler(sig, frame):
#   Raise a TimeoutException when the function takes too long
    raise TimeoutException

def hex_to_bytes(data: str) -> bytes:
#   Remove spaces from the hex string and convert it to bytes
    data = data.replace(" ", "")
    return bytes.fromhex(data)

def generate_totp(ua: str):
#   Function creating a TOTP object using a secret derived from transformed cipher bytes
    secret_cipher_bytes = [
        12, 56, 76, 33, 88, 44, 88, 33,
        78, 78, 11, 66, 22, 22, 55, 69, 54,
    ]

    transformed = [e ^ ((t % 33) + 9) for t, e in enumerate(secret_cipher_bytes)]
    joined = "".join(str(num) for num in transformed)
    utf8_bytes = joined.encode("utf-8")
    hex_str = "".join(format(b, 'x') for b in utf8_bytes)
    secret_bytes = hex_to_bytes(hex_str)
    secret = base64.b32encode(secret_bytes).decode().rstrip('=')

    headers = {
        "Host": "open.spotify.com",
        "User-Agent": ua,
        "Accept": "*/*",
    }

    try:
        if platform.system() != 'Windows':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(FUNCTION_TIMEOUT + 2)
        resp = req.get(SERVER_TIME_URL, headers=headers, timeout=FUNCTION_TIMEOUT, verify=VERIFY_SSL)
    except (req.RequestException, TimeoutException) as e:
        raise Exception(f"generate_totp() network request timeout: {e}")
    finally:
        if platform.system() != 'Windows':
            signal.alarm(0)

    resp.raise_for_status()

    json_data = resp.json()
    server_time = json_data.get("serverTime")

    if server_time is None:
        raise Exception("Failed to get server time")

    totp_obj = pyotp.TOTP(secret, digits=6, interval=30)
    return totp_obj, server_time

def write_token(new_token, retries=3):
#   Write the token to the file.
#   Retry if the file is locked by another process.
    for attempt in range(retries):
        try:
            with open('token.txt', 'w') as file:
                file.write(new_token)
            return  # Success: exit the function.
        except IOError as e:
            if attempt < retries - 1:
                time.sleep(0.5)  # Wait before retrying.
            else:
                raise Exception(f"Failed to write token after {retries} attempts: {e}")

ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
totp = generate_totp(ua)[0].now()
headers = {
    "Accept": "*/*",
    "User-Agent": ua,
    "Cookie": f"sp_dc={SP_DC}",
}
params = {
    "reason": "transport",
    "productType": "web_player",
    "totp": totp,
    "totpServer": totp,
    "totpVer": 5,
    "sTime": generate_totp(ua)[1],
    "cTime": int(time_ns() / 1000 / 1000),
}

# Get the client ID and access token using the generated TOTP, server time and the SP_DC cookie
resp = req.get("https://open.spotify.com/get_access_token", headers=headers, params=params, timeout=FUNCTION_TIMEOUT, verify=VERIFY_SSL)

clientId = resp.json().get("clientId")
token = resp.json().get("accessToken")

# Pass the clientId and the token to the getFriendFeed endpoint
print(clientId)
print(token)

write_token(token)