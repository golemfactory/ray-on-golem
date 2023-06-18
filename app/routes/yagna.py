from aiohttp import web

routes = web.RouteTableDef()


@routes.get('/payment')
async def yagna_setup_payment(request):
    pass


@routes.get('/identity')
async def yagna_setup_identity(request):
    pass
