import imghdr

from aiohttp import web
import aiohttp_jinja2

from bd_routines import send_request
from authentication_routines import login_to_token, check_authorisation


MAX_IMG_SIZE = 1 * 10 ** 6


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
            file = '/index.html'
            context = {"authorised": True}

    text = aiohttp_jinja2.render_string(file, request, context)
    response.text = text
    return response


@post_routes.post("/add_herb")
@aiohttp_jinja2.template('add_herb')
async def post_add_herb(request):
    context = {}
    user = await check_authorisation(request)
    if not user:
        context['user_error'] = True
        return context

    reader = await request.multipart()

    field = await reader.next()
    assert field.name == 'name'
    name = await field.read(decode=True)

    field = await reader.next()
    assert field.name == 'latin_name'
    latin_name = await field.read(decode=True)

    field = await reader.next()
    assert field.name == 'description'
    description = await field.read(decode=True)

    field = await reader.next()
    assert field.name == 'image'
    #filename = field.filename
    size = 0
    f = bytearray()
    while True:
        chunk = await field.read_chunk()  # 8192 bytes by default.
        if not size and not imghdr.what("", chunk):
            context['not_img'] = True
            return context
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_IMG_SIZE:
            context['too_big'] = True
            return context
        f.extend(chunk)

    await send_request(request.app,
                       "INSERT INTO Herb (name, latin_name, description, user_id, image) "
                       "VALUES (?, ?, ?, ?, ?);",
                       name, latin_name, description, user.id, f,
                       commit=True
                       )
    return context
