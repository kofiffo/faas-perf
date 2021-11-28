from minio import Minio
from PIL import Image
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config
from kafka import (KafkaProducer, KafkaAdminClient)
from kafka.admin import NewPartitions
from kafka.errors import InvalidPartitionsError
import cv2 as cv
import numpy as np
import os
import requests
import base64
import io
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
                'reporting_host': 'jaeger-udp.default.svc.cluster.local',
                'reporting_port': '6831',
            },
            'logging': True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()


tracer = init_tracer("paragraph")


def handle(event, context):
    with tracer.start_active_span("paragraph") as scope:
        req = event["data"]

        client = Minio(os.environ['minio_hostname'],
                       access_key=os.environ['minio_access_key'],
                       secret_key=os.environ['minio_secret_key'],
                       secure=False)

        imgdata = base64.b64decode(req)
        image = np.array(Image.open(io.BytesIO(imgdata)))
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (7, 7), 0)
        thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

        kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
        dilate = cv.dilate(thresh, kernel, iterations=3)

        cnts = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cnts = cnts[::-1]


        span = tracer.active_span
        headers = {}
        span.set_tag(tags.HTTP_URL, "http://merge.default.svc.cluster.local:8080")
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        with open("/tmp/span_context.txt", 'w') as f:
            f.write(str(headers))

        if not client.bucket_exists("context"):
            client.make_bucket("context")

        client.fput_object("context", "span_context.txt", "/tmp/span_context.txt")
        span.set_tag(tags.HTTP_METHOD, "GET")
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        # span.set_tag(tags.HTTP_URL, url)
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        if not client.bucket_exists("incoming"):
            client.make_bucket("incoming")

        invocation = os.getenv("INVOCATION", "sync")
        if invocation == "async":
            bootstrap_server = "kafka.kubeless.svc.cluster.local:9092"
            topic_name = "image-to-text-"

            # try:
            #     admin = KafkaAdminClient(bootstrap_servers=[bootstrap_server])
            #     partitions = {topic_name: NewPartitions(total_count=4)}
            #     admin.create_partitions(partitions)
            # except InvalidPartitionsError as e:
            #     print(e.message)

            producer = KafkaProducer(bootstrap_servers=[bootstrap_server],
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'))

        for i, c in enumerate(cnts):
            x, y, w, h = cv.boundingRect(c)
            cv.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
            p = gray[y:y + h, x:x + w]
            filename = f"paragraph_{i}.png"
            cv.imwrite(f"/tmp/{filename}", p)

            client.fput_object("incoming", filename, f"/tmp/{filename}")

            if invocation == "async":
                scope.span.log_kv({"event": f"sending_to_kafka_{i}"})
                producer.send(topic=f"{topic_name}{i}", value={"index": str(i), "headers": str(headers)})
            elif invocation == "sync":
                url = f"http://image-to-text-{i}.default.svc.cluster.local:8080"
                requests.post(url, data=str(i), headers=headers)
            else:
                raise Exception("The only valid INVOCATION value is \"async\". If no value is given, synchronous "
                                "invocation is used.")

        return "OK"
