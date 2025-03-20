from http import HTTPStatus

from fastapi import FastAPI

from subscription_control.router.catalog_engine import content_providers_router, product_handler_router

app = FastAPI(
    title='Subscription Control API',
    description='API for managing content provider subscriptions',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.include_router(content_providers_router)
app.include_router(product_handler_router)


@app.get(
    '/',
    status_code=HTTPStatus.OK,
    response_model=dict,
    tags=['Root'],
    summary='Root endpoint',
    description='Returns a welcome message',
)
def read_root():
    return {'message': 'Welcome to Subscription Control API'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app:app', host='127.0.0.1', port=8000, reload=True)
