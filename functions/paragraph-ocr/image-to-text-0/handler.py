from minio import Minio
from PIL import Image
import pytesseract
import os


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    filename = f"paragraph_{req}"
    client.fget_object("incoming", f"{filename}.png", f"/tmp/{filename}.png")

    text = pytesseract.image_to_string(Image.open(f"/tmp/{filename}.png"))

    with open(f"/tmp/{filename}.txt", 'w') as f:
        f.write(text)

    bucketname = f"bucket-{req}"

    if not client.bucket_exists(bucketname):
        client.make_bucket(bucketname)

    client.fput_object(bucketname, f"{filename}.txt", f"/tmp/{filename}.txt")

    return req