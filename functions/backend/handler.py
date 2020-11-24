import redis
import time

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
            #respond with the content of the request
            response = 'you said: ' + msg['data']
            r.publish('response_channel', response)

        time.sleep(0.001)

    return req
