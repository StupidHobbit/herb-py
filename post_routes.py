from aiohttp import web
import aiohttp_jinja2

from bd_routines import send_request
from authentication_routines import login_to_token


post_routes = web.RouteTableDef()


@post_routes.post("/login")
async def post_login(request):
    data = await request.post()
    login = data['login']
    password = data['password']

    response = web.Response()
    response.content_type = 'text/html'

    ans = await send_request(request.app,
                             "SELECT * FROM \"User\" WHERE login=? AND password=?;",
                             login, password)
    if len(ans):
        user = ans[0]
        token = login_to_token(request, login)
        response.set_cookie('token', token)
        context = {"authorised": True}
    else:
        context = {"warning": True}
    text = aiohttp_jinja2.render_string('index.html', request, context)
    response.text = text
    return response


@post_routes.post("/registration")
async def post_registration(request):
    data = await request.post()
    login = data['login']
    password = data['password']
    password_copy = data['password_copy']

    response = web.Response()
    response.content_type = 'text/html'
    file = '/registration'

    if password != password_copy:
        context = {"wrong_password": True}
    else:
        ans = await send_request(request.app,
                                 "SELECT * FROM \"User\" WHERE login=?;",
                                 login)
        if len(ans):
            user = ans[0]
            context = {"user_exists": True}
        else:
            token = login_to_token(request, login)
            response.set_cookie('token', token)
            await send_request(request.app,
                               "INSERT INTO \"User\" (login, password) VALUES (?, ?);",
                               login, password,
                               commit=True
                               )
            file = 'index.html'
            context = {"authorised": True}

    text = aiohttp_jinja2.render_string(file, request, context)
    response.text = text
    return response
