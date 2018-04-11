from cryptography.fernet import InvalidToken

from bd_routines import send_request


def token_to_login(request, token):
    try:
        login = request.app['cipher'].decrypt(token.encode()).decode()
    except InvalidToken:
        login = None
    return login


def login_to_token(request, login):
    token = request.app['cipher'].encrypt(login.encode()).decode()
    return token


async def check_authorisation(request):
    token = request.cookies.get("token")
    if not token:
        return

    login = token_to_login(request, token)
    if not login:
        return

    ans = await send_request(request.app,
                             "SELECT id, password FROM \"User\" WHERE login=?;",
                             login)
    if len(ans):
        return ans[0]
