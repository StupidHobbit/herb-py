from cryptography.fernet import InvalidToken, Fernet

from bd_routines import send_request


async def init_cryptography(app):
    cipher_key = Fernet.generate_key()
    salt = Fernet.generate_key()
    cipher = Fernet(cipher_key)
    app['cipher'] = cipher
    app['salt'] = salt


def token_to_login(request, token):
    cipher, salt = request.app['cipher'], request.app['salt']
    try:
        login = cipher.decrypt(token.encode()).decode()[:-len(salt)]
    except InvalidToken:
        login = None
    return login


def login_to_token(request, login):
    cipher, salt = request.app['cipher'], request.app['salt']
    token = cipher.encrypt(login.encode()+salt).decode()
    return token


async def check_authorisation(request):
    token = request.cookies.get("token")
    if not token:
        return

    login = token_to_login(request, token)
    if not login:
        return

    ans = await send_request(request.app,
                             "SELECT id, login, password FROM \"User\" WHERE login=?;",
                             login)
    if len(ans):
        return ans[0]
    return
