import requests
import sys
import os
import time
import opentracing
import logging
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

tracer = init_tracer('frontend')

def handle(req):
    with tracer.start_span('frontend') as span:
        span.log_kv({'event': 'call_backend'})

        gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")

        body = req

        #trigger the backend function
        r = requests.get("http://" + gateway_hostname + ":8080/function/backend", data = body)

        if r.status_code != 200:
            sys.exit("Error with backend, expected: %d, got: %d\n" % (200, r.status_code))

        return r.content