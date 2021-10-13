from minio import Minio
from PIL import Image
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config
from flask import request
import logging
import pytesseract
import os
import requests


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


tracer = init_tracer("image-to-text")


def handle(req):
    span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}

    with tracer.start_active_span(f"image-to-text-{req}", child_of=span_ctx, tags=span_tags) as scope:

        scope.span.log_kv({"event": "mc_setup"})

        client = Minio(os.environ['minio_hostname'],
                       access_key=os.environ['minio_access_key'],
                       secret_key=os.environ['minio_secret_key'],
                       secure=False)

        # object_list = list(client.list_objects("incoming"))
        # last_object_name = object_list[-1].object_name.split('.')[0]
        # last_index = int(last_object_name[-1])

        scope.span.log_kv({"event": "get_object"})

        filename = f"paragraph_{req}"
        client.fget_object("incoming", f"{filename}.png", f"/tmp/{filename}.png")

        scope.span.log_kv({"event": "image_to_string"})

        text = pytesseract.image_to_string(Image.open(f"/tmp/{filename}.png"))

        scope.span.log_kv({"event": "put_object"})

        with open(f"/tmp/{filename}.txt", 'w') as file:
            file.write(text)

        if not client.bucket_exists("paragraphs"):
            client.make_bucket("paragraphs")

        client.fput_object("paragraphs", f"{filename}.txt", f"/tmp/{filename}.txt")

        scope.span.log_kv({"event": "check_size_of_paragraph_bucket"})

        if len(list(client.list_objects("paragraphs"))) == 4:
            gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
            url = f"http://{gateway_hostname}:8080/async-function/merge"

            scope.span.log_kv({"event": "invoke_merge_function"})
            requests.post(url)

        return req
