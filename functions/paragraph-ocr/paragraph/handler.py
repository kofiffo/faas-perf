from minio import Minio
from PIL import Image
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config
import cv2 as cv
import numpy as np
import os
import requests
import base64
import io
import logging
import threading


def invoke_function(url, index, headers):
    requests.post(url, data=str(index), headers=headers)


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


tracer = init_tracer("paragraph")


def handle(req):
    with tracer.start_active_span("paragraph") as scope:
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
        cnts.reverse()

        gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
        url = f"http://{gateway_hostname}:8080/async-function/image-to-text-0"

        span = tracer.active_span
        span.set_tag(tags.HTTP_METHOD, "GET")
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        span.set_tag(tags.HTTP_URL, url)
        headers = {}
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        threads = []
        idx = 0

        if not client.bucket_exists("incoming"):
            client.make_bucket("incoming")

        for c in cnts:
            x, y, w, h = cv.boundingRect(c)
            cv.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
            p = gray[y:y + h, x:x + w]
            filename = f"paragraph_{idx}.png"
            cv.imwrite(f"/tmp/{filename}", p)

            client.fput_object("incoming", filename, f"/tmp/{filename}")

            # requests.post(url, data=str(idx), headers=headers)

            t = threading.Thread(target=invoke_function(url, idx, headers))
            threads.append(t)
            idx += 1

        span.set_tag(tags.HTTP_URL, f"http://{gateway_hostname}:8080/function/merge)")
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        with open("/tmp/span_context.txt", 'w') as f:
            f.write(str(headers))

        if not client.bucket_exists("context"):
            client.make_bucket("context")

        client.fput_object("context", "span_context.txt", "/tmp/span_context.txt")

        for th in threads:
            th.start()

        for th in threads:
            th.join()

        return req
