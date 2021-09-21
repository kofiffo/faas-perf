from minio import Minio
import cv2 as cv
import os
import imutils


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    client.fget_object("incoming", "q_2.png", "/tmp/q_2.png")

    img = cv.imread("/tmp/q_2.png")
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    img = cv.resize(img, (h//2, w//2), interpolation=cv.INTER_LINEAR)
    img = imutils.rotate_bound(img, -90)

    cv.imwrite("/tmp/q_2.png", img)

    if not client.bucket_exists("processed"):
        client.make_bucket("processed")
    else:
        print(f"Bucket 'processed' already exists.")

    client.fput_object("processed", "q_2.png", "/tmp/q_2.png")

    return req
