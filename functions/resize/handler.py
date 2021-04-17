from PIL import Image
from minio import Minio
import os


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    client.fget_object("incoming", "image.png", "/tmp/image.png")

    img = Image.open("/tmp/image.png")
    img = img.resize((img.width // 2, img.height // 2))
    img.save("/tmp/image.png")

    client.fput_object("processed", "image.png", "/tmp/image.png")

    return req
