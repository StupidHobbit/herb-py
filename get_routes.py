from aiohttp import web
import aiohttp_jinja2

from bd_routines import send_request
from authentication_routines import check_authorisation


get_routes = web.RouteTableDef()


@get_routes.get("/herbs")
@aiohttp_jinja2.template('herbs')
async def get_herbs(request):
    char = request.query.get('char')
    if char and char in request.app["alphabet"]:
        herbs = await send_request(request.app,
                                   "SELECT ID, name, latin_name, description "
                                   "FROM Herb "
                                   "WHERE name LIKE '%s%%' "
                                   "ORDER BY name;"
                                   % char)
    else:
        herbs = await send_request(request.app,
                                   "SELECT ID, name, latin_name, description "
                                   # "SELECT ID, name, COALESCE(latin_name, ''), coalesce(description, '') "
                                   "FROM Herb "
                                   "ORDER BY name;")
    return {'herbs': herbs, 'alphabet': request.app['alphabet']}


@get_routes.get("/")
@aiohttp_jinja2.template('index.html')
async def intro(request):
    authorised = bool(await check_authorisation(request))
    return {'authorised': authorised}


@get_routes.get("/registration")
@aiohttp_jinja2.template('registration')
async def get_registration(request):
    return {}


@get_routes.get("/images/herb_{ID}.jpg")
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
