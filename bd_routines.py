from pyodbc import ProgrammingError
import aioodbc


async def init_db(app):
    conf = app['config']['postgres']
    dsn = ("DRIVER=%s;"
           "DATABASE=%s;"
           "UID=%s;"
           "PWD=%s;"
           "SERVER=%s;"
           "PORT=%s"
           % (conf['driver'],
              conf['database'],
              conf['user'],
              conf['password'],
              conf['host'],
              conf['port'])
           )
    engine = await aioodbc.create_pool(dsn=dsn, loop=app.loop)
    app['db'] = engine


async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()


async def send_request(app, request, *args, commit=False):
    #print(request)
    async with app['db'].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(request, args)
            if commit:
                await cur.commit()
            try:
                ans = await cur.fetchall()
            except ProgrammingError:
                ans = []

    return ans