import base64
import hashlib
import uuid
from datetime import datetime

import httpx
from dateutil import parser
from zoneinfo import ZoneInfo

from src.config.config import WIX_CLIENT_ID


def generate_code_challenge(code_verifier: str) -> str:
    # SHA-256
    hashed_verifier = hashlib.sha256(code_verifier.encode()).digest()

    # Base64
    code_challenge = base64.urlsafe_b64encode(hashed_verifier).rstrip(b"=")
    return code_challenge.decode("utf-8")


async def wix_get_callback_url(username: str, password: str, state: str):
    code_verifier = str(uuid.uuid4()).replace("-", "")

    login_url = "https://www.wixapis.com/_api/iam/authentication/v2/login"
    redirect_url = "https://www.wixapis.com/_api/redirects-api/v1/redirect-session"

    data = {"loginId": {"email": username}, "password": password}

    async with httpx.AsyncClient() as client:
        anonymous_response = await client.post(
            "https://www.wixapis.com/oauth2/token",
            headers={
                "content-type": "application/json",
            },
            json={"clientId": WIX_CLIENT_ID, "grantType": "anonymous"},
        )
        anonymous_access_token = anonymous_response.json()["access_token"]

        headers = {
            "authorization": anonymous_access_token,
            "content-type": "application/json",
        }

        session_token_response = await client.post(
            login_url, headers=headers, json=data
        )

        try:
            response_text = session_token_response.json()
        except (httpx.JSONDecodeError, ValueError):
            return None

        if response_text.get("state") != "SUCCESS":
            return None

        session_token = response_text["sessionToken"]
        code_challenge = generate_code_challenge(code_verifier)

        redirect_data = {
            "auth": {
                "authRequest": {
                    "clientId": WIX_CLIENT_ID,
                    "codeChallenge": code_challenge,
                    "codeChallengeMethod": "S256",
                    "responseMode": "web_message",
                    "responseType": "code",
                    "scope": "offline_access",
                    "state": state,
                    "sessionToken": session_token,
                }
            }
        }

        redirect_response = await client.post(
            redirect_url, headers=headers, json=redirect_data
        )

        try:
            url_response = redirect_response.json()["redirectSession"]["fullUrl"]
        except Exception:
            return None

    return url_response, code_verifier


async def get_member_access_token(code: str, code_verifier: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.wixapis.com/oauth2/token",
            headers={"content-type": "application/json"},
            json={
                "client_id": WIX_CLIENT_ID,
                "grant_type": "authorization_code",
                "code": code,
                "codeVerifier": code_verifier,
            },
        )
    member_access_token = response.json().get("access_token")

    return member_access_token


def get_highest_active_subscription(orders):
    # Define priority levels
    priority = {"Elite": 3, "Pro": 2, "Basic": 1}

    # Find all orders with "ACTIVE" status
    active_orders = [order for order in orders if order["status"] == "ACTIVE"]

    if not active_orders:
        return None

    # Get the order with the highest level
    highest_order = max(active_orders, key=lambda x: priority.get(x["planName"], 0))

    end_date = parser.parse(highest_order["endDate"])
    current_date = datetime.now(ZoneInfo("UTC"))
    time_difference = end_date - current_date
    expires_in = str(int(time_difference.total_seconds()))

    return highest_order["planName"], expires_in


async def wix_get_subscription(member_access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        orders_response = await client.get(
            "https://www.wixapis.com/pricing-plans/v2/member/orders",
            headers={"authorization": member_access_token},
        )
    orders = orders_response.json()["orders"]

    subscription, expires_in = get_highest_active_subscription(orders)

    return subscription, expires_in
