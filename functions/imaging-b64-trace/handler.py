import requests
import os
import base64
from io import BytesIO
import logging
from opentracing.ext import tags
from opentracing.propagation import Format
from jaeger_client import Config

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

tracer = init_tracer('imaging-b64')


def handle(req):
    with tracer.start_active_span('imaging-b64') as scope:
        try:
            scope.span.log_kv({'event': 'download_image'})
            r = requests.get(req)

            scope.span.log_kv({'event': 'save_image'})
            image = BytesIO()
            image.write(r.content)

            scope.span.log_kv({'event': 'encode_image'})
            encoded_image = base64.b64encode(image.getvalue())

            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

            gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
            url = "http://" + gateway_hostname + ":8080/async-function/resize-b64-trace"

            scope.span.log_kv({'event': 'setup_context_injection'})
            span = tracer.active_span
            span.set_tag(tags.HTTP_METHOD, 'GET')
            span.set_tag(tags.HTTP_URL, url)
            span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
            scope.span.log_kv({'event': 'inject_span_context'})
            tracer.inject(span, Format.HTTP_HEADERS, headers)

            scope.span.log_kv({'event': 'call_resizing_function'})
            r = requests.post(url, data=encoded_image, headers=headers)
            resp = str(len(encoded_image)) + "\nOK"

        except Exception as e:
            resp = str(e)

        return resp
