from minio import Minio
import os


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    text = ""

    for i in range(4):
        bucketname = f"bucket-{i}"
        filename = f"paragraph_{i}.txt"

        client.fget_object(bucketname, filename, f"/tmp/{filename}")

        with open(f"/tmp/{filename}", 'r') as f:
            text = text + f.read() + '\n'

    with open("/tmp/text.txt", 'w') as f:
        f.write(text)

    if not client.bucket_exists("processed"):
        client.make_bucket("processed")

    client.fput_object("processed", "text.txt", "/tmp/text.txt")

    return req
