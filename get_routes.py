from aiohttp import web
import aiohttp_jinja2

from bd_routines import send_request
from authentication_routines import check_authorisation


get_routes = web.RouteTableDef()


@get_routes.get("/herbs")
@aiohttp_jinja2.template('herbs')
async def get_herbs(request):
    char = request.query.get('char')
    if char and char in request.app["herbs_alphabet"]:
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
    authorised = bool(await check_authorisation(request))
    return {'herbs': herbs,
            'alphabet': request.app['herbs_alphabet'],
            'authorised': authorised}


@get_routes.get("/herbs/{ID}")
@aiohttp_jinja2.template('herb')
async def get_herbs(request):
    herb_id = request.match_info["ID"]
    herb = await send_request(request.app,
                               "SELECT id, name, latin_name, description "
                               "FROM Herb "
                               "WHERE id=?",
                               herb_id)
    if not herb:
        return {'error': True}
    collections = await send_request(request.app,
                              "SELECT id, name "
                              "FROM Collection c, Item ct "
                              "WHERE c.id=ct.collection_id "
                              "AND   ?=ct.herb_id",
                              herb_id)
    return {'herb': herb[0],
            'collections': collections}


@get_routes.get("/collections")
@aiohttp_jinja2.template('collections')
async def get_collections(request):
    char = request.query.get('char')
    if char and char in request.app["collection_alphabet"]:
        collections = await send_request(request.app,
                                   "SELECT ID, name, latin_name, description "
                                   "FROM Collection "
                                   "WHERE name LIKE '%s%%' "
                                   "ORDER BY name;"
                                   % char)
    else:
        collections = await send_request(request.app,
                                   "SELECT ID, name, latin_name, description "
                                   # "SELECT ID, name, COALESCE(latin_name, ''), coalesce(description, '') "
                                   "FROM Collection "
                                   "ORDER BY name;")
    authorised = bool(await check_authorisation(request))
    return {'collection': collections,
            'alphabet': request.app['collection_alphabet'],
            'authorised': authorised}


@get_routes.get("/collection/{ID}")
@aiohttp_jinja2.template('collection')
async def get_collection(request):
    collection_id = request.match_info["ID"]
    collection = await send_request(request.app,
                               "SELECT id, name, latin_name, description, cooking_method "
                               "FROM Collection "
                               "WHERE id=?",
                               collection_id)
    if not collection:
        return {'error': True}
    herbs = await send_request(request.app,
                              "SELECT h.id, h.name, p.part,  CAST(round(ct.percentage*100) AS integer) AS percentage "
                              "FROM Herb h, Item ct, Part p "
                              "WHERE ?=ct.collection_id "
                              "AND   h.id=ct.herb_id "
                              "AND   ct.part_id=p.id",
                              collection_id)
    return {'herbs': herbs,
            'collection': collection[0]}


@get_routes.get("/")
@aiohttp_jinja2.template('index.html')
async def intro(request):
    authorised = bool(await check_authorisation(request))
    return {'authorised': authorised}


@get_routes.get("/add_herb")
@aiohttp_jinja2.template('add_herb')
async def get_add_herb(request):
    authorised = bool(await check_authorisation(request))
    return {'authorised': authorised}


@get_routes.get("/registration")
@aiohttp_jinja2.template('registration')
async def get_registration(request):
    return {}





@get_routes.get("/images/herb_{ID}")
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
