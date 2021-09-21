from PIL import Image
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

tracer = init_tracer('resize-raw')


def handle(req):
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}
    with tracer.start_active_span('resize', child_of=span_ctx, tags=span_tags):
        # save incoming image data to file
        with open("image.png", "wb") as file:
            file.write(req)

        # make image out of file
        img = Image.open("image.png")
        # resize image
        img = img.resize((img.width // 2, img.height // 2))
        resp = str(img.format) + ' ' + str(img.size) + ' ' + str(img.mode)

        return resp
