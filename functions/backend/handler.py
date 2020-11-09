import redis
import time

def handle(req):

    #subscribe to the mutual channel
    r = redis.Redis(host='10.106.58.121', port=6379, db=0)
    p = r.pubsub(ignore_subscribe_messages=True)
    p.subscribe('redis_channel')

    response = ''

    #take requests
    while True:
        msg = p.get_message()
        if msg:
            #respond with the content of the request
            response = 'you said: ' + msg['data']
            r.publish('redis_channel', response)

        time.sleep(0.001)

    return req
