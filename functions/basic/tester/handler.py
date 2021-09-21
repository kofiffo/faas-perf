import requests
import sys
import os
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


tracer = init_tracer('frontend')


def handle(req):
    with tracer.start_active_span('frontend') as scope:
        scope.span.log_kv({'event': 'set_gateway'})
        gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
        url = "http://" + gateway_hostname + ":8080/function/backend"

        scope.span.log_kv({'event': 'set_request_body'})
        body = req

        scope.span.log_kv({'event': 'setup_context_injection'})
        span = tracer.active_span
        span.set_tag(tags.HTTP_METHOD, 'GET')
        span.set_tag(tags.HTTP_URL, url)
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        headers = {}
        scope.span.log_kv({'event': 'inject_span_context'})
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        scope.span.log_kv({'event': 'call_backend'})
        r = requests.get(url, data=body, headers=headers)

        scope.span.log_kv({'event': 'check_status_code'})
        if r.status_code != 200:
            scope.span.log_kv({'event': 'exit_due_to_error'})
            sys.exit("Error with backend, expected: %d, got: %d\n" % (200, r.status_code))

        return r.content
