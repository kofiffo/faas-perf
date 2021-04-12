from PIL import Image
import requests
import os


def handle(req):
    try:
        img = Image.open(requests.get(req, stream=True).raw)

        gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
        url = "http://" + gateway_hostname + ":8080/function/resize"

        r = requests.post(url, data=img.tobytes())
        resp = r.text

    except Exception as e:
        resp = str(e)

    return resp
