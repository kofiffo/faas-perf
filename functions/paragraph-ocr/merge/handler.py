from minio import Minio
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config
import os
import logging
import json


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


tracer = init_tracer("merge")


def handle(req):
    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    client.fget_object("context", "span_context.txt", "/tmp/span_context.txt")

    with open("/tmp/span_context.txt", 'r') as f:
        headers = json.loads(f.read().replace('\'', '\"'))

    span_ctx = tracer.extract(Format.HTTP_HEADERS, headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}

    with tracer.start_active_span("merge", child_of=span_ctx, tags=span_tags):
        text = ""

        for i in range(4):
            filename = f"paragraph_{i}.txt"

            client.fget_object("paragraphs", filename, f"/tmp/{filename}")

            with open(f"/tmp/{filename}", 'r') as f:
                text = text + f.read() + '\n'

        with open("/tmp/text.txt", 'w') as f:
            f.write(text)

        if not client.bucket_exists("processed"):
            client.make_bucket("processed")

        client.fput_object("processed", "text.txt", "/tmp/text.txt")

        for obj in client.list_objects("paragraphs"):
            client.remove_object("paragraphs", obj.object_name)
        client.remove_bucket("paragraphs")

        return req
