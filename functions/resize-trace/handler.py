from PIL import Image
from minio import Minio
import os
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

tracer = init_tracer('resize')


def handle(req):
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}
    with tracer.start_active_span('resize', child_of=span_ctx, tags=span_tags):

        client = Minio(os.environ['minio_hostname'],
                       access_key=os.environ['minio_access_key'],
                       secret_key=os.environ['minio_secret_key'],
                       secure=False)

        client.fget_object("incoming", "image.png", "/tmp/image.png")

        img = Image.open("/tmp/image.png")
        img = img.resize((img.width // 2, img.height // 2))
        img.save("/tmp/image.png")

        client.fput_object("processed", "image.png", "/tmp/image.png")

        return req
