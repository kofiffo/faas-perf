import requests
import sys
import os


def handle(req):
    gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
    url = "http://" + gateway_hostname + ":8080/function/backend-notrace"

    body = req

    r = requests.get(url, data=body)

    if r.status_code != 200:
        sys.exit("Error with backend, expected: %d, got: %d\n" % (200, r.status_code))

    return r.content
