import redis
import time

def handle(req):

    #trigger the backend function through the redis channel
    r = redis.Redis(host='10.106.58.121', port=6379, db=0)
    r.publish('redis_channel', req)

    #subscribe to the same channel and wait for the response
    p = r.pubsub(ignore_subscribe_messages=True)
    p.subscribe('redis_channel')

    #wait for response
    while(True):
        response = p.get_message()
        if response:
            break

        time.sleep(0.001)

    return response['data']

