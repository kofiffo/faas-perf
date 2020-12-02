import redis
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
                'reporting_host': '10.107.197.168',
                'reporting_port': '6831',
            },
            'logging': True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer('backend')

def handle(req):

    #subscribe to the mutual channel
    r = redis.Redis(host='10.99.192.111', port=6379, db=0)
    p = r.pubsub(ignore_subscribe_messages=True)
    p.subscribe('request_channel')

    response = ''

    #take requests
    while True:
        msg = p.get_message()
        if msg:
            with tracer.start_span('send_response') as span:
                #respond with the content of the request
                response = 'you said: ' + msg['data']
                r.publish('response_channel', response)

        time.sleep(0.001)

    # yield to IOLoop to flush the spans
    time.sleep(2)
    tracer.close()

    return req
