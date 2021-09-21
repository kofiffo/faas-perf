from minio import Minio
import requests
import os


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    r = requests.get(req)

    with open("/tmp/image.png", "wb") as file:
        file.write(r.content)

    if not client.bucket_exists("incoming"):
        client.make_bucket("incoming")
    else:
        print("Bucket 'incoming' already exists.")

    client.fput_object("incoming", "image.png", "/tmp/image.png")

    gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
    url = "http://" + gateway_hostname + ":8080/function/resize"

    r = requests.post(url)

    return req
