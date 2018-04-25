import imghdr
from itertools import count

from aiohttp import web
import aiohttp_jinja2
from pyodbc import IntegrityError

from bd_routines import send_request
from authentication_routines import login_to_token, check_authorisation


MAX_IMG_SIZE = 0.3 * 10 ** 6


post_routes = web.RouteTableDef()


@post_routes.post("/login")
async def post_login(request):
    data = await request.post()
    login = data['login']
    password = data['password']

    headers = {"Location": "/#intro"}
    response = web.Response(headers=headers)
    response.content_type = 'text/html'

    ans = await send_request(request.app,
                             "SELECT * FROM \"User\" WHERE login=? AND password=?;",
                             login, password)
    if len(ans):
        user = ans[0]
        token = login_to_token(request, login)
        response.set_cookie('token', token)
        response.set_status(303)
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

    headers = {"Location": "/#intro"}
    response = web.Response(headers=headers)
    response.content_type = 'text/html'
    file = '/registration'

    if password != password_copy:
        context = {"wrong_password": True}
    else:
        try:
            await send_request(request.app,
                               "INSERT INTO \"User\" (login, password) VALUES (?, ?);",
                               login, password,
                               commit=True)
            token = login_to_token(request, login)
            response.set_status(303)
            return response
        except IntegrityError:
            context = {"user_exists": True}

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
    filename = field.filename
    f = bytearray()
    if filename:
        size = 0
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

    try:
        await send_request(request.app,
                       "INSERT INTO Herb (name, latin_name, description, user_id, image) "
                       "VALUES (?, ?, ?, ?, ?);",
                       name, latin_name, description, user.id, f,
                       commit=True
                       )
    except IntegrityError:
        context['already_exists'] = True
    return context


@post_routes.post("/add_collection")
@aiohttp_jinja2.template('add_collection')
async def post_add_collection(request):
    context = {}
    user = await check_authorisation(request)
    if not user:
        context['user_error'] = True
        #return context

    data = await request.post()
    name = data["name"]
    latin_name = data["latin_name"]
    disease = data["disease"]
    description = data["description"]
    cooking = data["cooking"]
    disease = await send_request(request.app,
                       "SELECT id "
                       "FROM Disease "
                       "WHERE name = ?;",
                       disease)
    if not disease:
        #context['disease_not_found'] = True
        #return context
        disease_id = None
    else:
        disease_id = disease[0].id

    try:
        await send_request(request.app,
                       "INSERT INTO Collection "
                       "(name, latin_name, description, user_id, cooking_method, disease_id) "
                       "VALUES (?, ?, ?, ?, ?, ?);",
                       name, latin_name, description, user.id, cooking, disease_id,
                       commit=True
                       )
    except IntegrityError:
        context['already_exist'] = True
        return context

    collection = await send_request(request.app,
                                    "SELECT id "
                                    "FROM Collection "
                                    "WHERE name = ?",
                                    name)
    print(collection)
