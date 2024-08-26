import uuid

import redis
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from src.config.config import CLIENT_ID, CLIENT_SECRET, FASTAPI_BEARER_TOKEN
from src.models.models import SubscriptionRequest
from src.services.wix.wix_oauth import (
    get_member_access_token,
    wix_get_callback_url,
    wix_get_subscription,
)

router = APIRouter()

templates = Jinja2Templates(directory="templates")

r = redis.Redis(host="localhost", port=6379, db=0)


def get_oauth_params(
    response_type: str = Query(...),
    client_id: str = Query(...),
    state: str = Query(...),
    redirect_uri: str = Query(...),
) -> dict:
    return {
        "response_type": response_type,
        "client_id": client_id,
        "state": state,
        "redirect_uri": redirect_uri,
    }


async def get_session_data(request: Request):
    return request.session


@router.get("/login/")
async def login(
    request: Request,
    oauth_params: dict = Depends(get_oauth_params),
    session_data: dict = Depends(get_session_data),
):
    session_data.update(oauth_params)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login/")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session_data: dict = Depends(get_session_data),
):
    # response_type = session_data.get("response_type")
    # client_id = session_data.get("client_id")
    # scope = session_data.get("scope")
    state = session_data.get("state")
    # redirect_uri = session_data.get("redirect_uri")

    result = await wix_get_callback_url(
        username=username, password=password, state=state
    )

    if result is None:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "User not registered!"}
        )

    wix_callback_url, code_verifier = result
    session_data["wix_callback_url"] = wix_callback_url
    session_data["code_verifier"] = code_verifier

    # redirect to callback url
    raise HTTPException(
        status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "../callback/"}
    )


@router.get("/callback/")
async def callback(request: Request, session_data: dict = Depends(get_session_data)):
    wix_callback_url = session_data.get("wix_callback_url")

    return templates.TemplateResponse(
        "callback.html",
        {
            "request": request,
            "wix_callback_url": wix_callback_url,
        },
    )


@router.post("/callback/")
async def subscription(
    request: SubscriptionRequest, session_data: dict = Depends(get_session_data)
):
    try:
        state = session_data.get("state")
        redirect_uri = session_data.get("redirect_uri")
        # state from wix
        openai_code = str(uuid.uuid4())
        url = redirect_uri + f"?state={state}&code={openai_code}"

        wix_code = request.code

        member_access_token = await get_member_access_token(
            wix_code, session_data["code_verifier"]
        )

        result = await wix_get_subscription(member_access_token)

        if result is not None:
            subscription, expires_in = result

            r.set(openai_code, expires_in, ex=1800)

            if subscription == "Basic":
                message = "You are a Basic subscriber."
            elif subscription == "Pro":
                message = "You are a Pro subscriber."
            elif subscription == "Elite":
                message = "You are an Elite subscriber."
        else:
            message = "It seems you are not subscribed yet. Please visit our website for more information."
            url = "https://www.kaiwu.info"

        return JSONResponse(content={"message": message, "url": url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authorization/")
async def authorization(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: str = Form(...),
):
    expires_in = int(r.get(code))
    if client_id != CLIENT_ID or client_secret != CLIENT_SECRET or expires_in is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {
        "access_token": FASTAPI_BEARER_TOKEN,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
