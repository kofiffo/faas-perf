from PIL import Image
import base64
import logging
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config
from flask import request


def init_tracer(service):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'local_agent': {
                'reporting_host': '10.100.179.158',
                'reporting_port': '6831',
            },
            'logging': True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer('resize-b64')


def handle(req):
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}
    with tracer.start_active_span('resize-b64', child_of=span_ctx, tags=span_tags):
        try:
            with open("image.png", 'wb') as file:
                file.write(base64.b64decode(req))

            img = Image.open("image.png")
            img = img.resize((img.width // 2, img.height // 2))
            resp = str(img.format) + ' ' + str(img.size) + ' ' + str(img.mode)
        except Exception as e:
            resp = str(e)

        return resp
