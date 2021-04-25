import requests
import os
import base64


def handle(req):
    try:
        r = requests.get(req)

        with open("image.png", "wb") as file:
            file.write(r.content)

        with open("image.png", "rb") as file:
            encoded_image = base64.b64encode(file.read())

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
        url = "http://" + gateway_hostname + ":8080/function/resize-b64"

        r = requests.post(url, data=encoded_image, headers=headers)
        resp = r.text

    except Exception as e:
        resp = str(e)

    return resp
