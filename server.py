from asyncio import sleep
import pathlib
from cryptography.fernet import Fernet
from sys import stdin

from aiohttp import web
import jinja2
import aiohttp_jinja2
import aioodbc
import aiofiles
from yaml import load, Loader
import aiopg

routes = web.RouteTableDef()


async def send_request(app, request, *args):
    print(request)
    async with app['db'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(request, args)
            ans = await cur.fetchall()
    return ans


@routes.get("/herbs")
@aiohttp_jinja2.template('herbs')
async def handler(request):
    char = request.query.get('char')
    if char and char in request.app["alphabet"]:
        herbs = await send_request(request.app,
                               "SELECT ID, name, Latin_name FROM Herb WHERE name LIKE '%s%%' ORDER BY name;"
                                % char)
    else:
        herbs = await send_request(request.app,
                                   "SELECT ID, Name, Latin_name FROM Herb ORDER BY name;")
    return {'herbs': herbs, 'alphabet': request.app['alphabet']}


@routes.post("/login")
async def name(request):
    data = await request.post()
    login = data['login']
    password = data['password']
    response = web.Response()
    response.content_type = 'text/html'
    try:
        ans = await send_request(request.app,
                                 "SELECT * FROM User WHERE login=? AND password=?;",
                                 login, password)
        user = ans[0]
        token = request.app['cipher'].encrypt(login.encode())
        response.set_cookie('token', token)
        context = {"success": True}
    except IndexError:
        context = {"warning": True}
    finally:
        text = aiohttp_jinja2.render_string('index.html', request, context)
        response.text = text
        return response


@routes.get("/")
@aiohttp_jinja2.template('index.html')
async def intro(request):
    return {}


@routes.get("/login")
@aiohttp_jinja2.template('login_form')
async def image(request):
    return {}


@routes.get("/images/herb_{ID}.jpg")
async def image_get(request):
    if request.if_modified_since:
        return web.Response(status=304)
    ans = await send_request(request.app,
                             "SELECT Image FROM Herb WHERE ID = ?;",
                             request.match_info["ID"])
    content = ans[0][0]
    headers = {'Cache-Control': 'public, max-age=31536000',
               'Last-Modified': 'Fri, 30 Mar 2018 01:03:50 GMT'}
    return web.Response(body=content, headers=headers)


@routes.get("/big_request")
async def big_request(request):
    await sleep(5)
    return web.Response(text="Hello, &!#!$")


def load_config(file="polls.yaml"):
    stream = open(str(pathlib.Path('.') / 'config' / file))
    conf = load(stream, Loader)
    return conf


def init_func(argv):
    app = web.Application()

    app['config'] = load_config()

    app.router.add_routes(routes)
    app.router.add_static('/static', 'static', append_version=True)
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('templates'))

    cipher_key = Fernet.generate_key()
    cipher = Fernet(cipher_key)
    app['cipher'] = cipher

    app.on_startup.append(init_db)
    app.on_startup.append(init_alphabet)
    app.on_cleanup.append(init_db)

    return app


async def init_db(app):
    conf = app['config']['postgres']
    dsn = ("DRIVER={PostgreSQL Unicode};"
           "DATABASE=herbs;"
           "UID=postgres;"
           "PWD=1010;"
           "SERVER=localhost;"
           "PORT=5432"
           )
    engine = await aioodbc.create_pool(dsn=dsn, loop=app.loop)
    app['db'] = engine


async def init_alphabet(app):
    ans = await send_request(app, "SELECT name FROM Herb;")
    alphabet = list(set(item[0][0].upper() for item in ans))
    alphabet.sort()
    print(alphabet)
    app['alphabet'] = alphabet


async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()
