from minio import Minio
from minio.notificationconfig import (NotificationConfig, SuffixFilterRule, QueueConfig)
from PIL import Image
import cv2 as cv
import numpy as np
import os
import requests
import base64
import io


def handle(req):

    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    # config = NotificationConfig(
    #     queue_config_list=[
    #         QueueConfig(
    #             "arn:minio:sqs::1:webhook",
    #             ["s3:ObjectCreated:*"],
    #             config_id="1",
    #             suffix_filter_rule=SuffixFilterRule(".txt"),
    #         ),
    #     ],
    # )
    #
    # client.set_bucket_notification("bucket-3", config)

    imgdata = base64.b64decode(req)
    image = np.array(Image.open(io.BytesIO(imgdata)))
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (7, 7), 0)
    thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    dilate = cv.dilate(thresh, kernel, iterations=3)

    cnts = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    cnts.reverse()

    paragraphs = []
    idx = 0

    gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
    url = f"http://{gateway_hostname}:8080/function/image-to-text-"

    for c in cnts:
        x, y, w, h = cv.boundingRect(c)
        cv.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
        p = gray[y:y + h, x:x + w]
        filename = f"paragraph_{idx}.png"
        paragraphs.append(p)
        cv.imwrite(f"/tmp/{filename}", p)

        if not client.bucket_exists("incoming"):
            client.make_bucket("incoming")

        client.fput_object("incoming", filename, f"/tmp/{filename}")
        requests.post(f"{url}{idx}", data=str(idx))

        idx += 1

    return req
