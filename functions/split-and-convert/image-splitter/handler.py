import cv2 as cv
import numpy as np
import os
import requests
import time
from minio import Minio


# define a function for vertically
# concatenating images of different
# widths
def vconcat_resize(img_list, interpolation=cv.INTER_CUBIC):
    # take minimum width
    w_min = min(im.shape[1]
                for im in img_list)

    # resizing images
    im_list_resize = [cv.resize(im,
                                (w_min, int(im.shape[0] * w_min / im.shape[1])),
                                interpolation=interpolation)
                      for im in img_list]
    # return final image
    return cv.vconcat(im_list_resize)


def handle(req):
    client = Minio(os.environ['minio_hostname'],
                   access_key=os.environ['minio_access_key'],
                   secret_key=os.environ['minio_secret_key'],
                   secure=False)

    r = requests.get(req)

    img_array = np.array(bytearray(r.content), dtype=np.uint8)
    img = cv.imdecode(img_array, -1)

    height_scale = img.shape[0] / 2
    width_scale = img.shape[1] / 2

    if isinstance(height_scale, float):
        height_scale = round(height_scale)

    if isinstance(width_scale, float):
        width_scale = round(width_scale)

    segments = []

    for r in range(0, img.shape[0], height_scale):
        for c in range(0, img.shape[1], width_scale):
            segments.append(img[r:r + height_scale, c:c + width_scale, :])

    quadrants = segments[:4]
    idx = 0

    for q in quadrants:
        cv.imwrite(f"/tmp/q_{idx}.png", q)

        if not client.bucket_exists("incoming"):
            client.make_bucket("incoming")
        else:
            print(f"Bucket 'incoming' already exists.")

        client.fput_object("incoming", f"q_{idx}.png", f"/tmp/q_{idx}.png")
        idx += 1

    gateway_hostname = os.getenv("gateway_hostname", "gateway.openfaas")
    url = f"http://{gateway_hostname}:8080/function/convert-2-"
    color_spaces = ["hsv", "lab", "rgb", "hls"]

    for space in color_spaces:
        requests.post(url + space)

    time.sleep(3)

    processed_segments = []

    for i in range(4):
        client.fget_object("processed", f"q_{i}.png", f"/tmp/q_{i}.png")
        processed_segments.append(cv.imread(f"/tmp/q_{i}.png"))

    img_h1 = cv.hconcat([processed_segments[0], processed_segments[2]])
    img_h2 = cv.hconcat([processed_segments[1], processed_segments[3]])
    img_v = vconcat_resize([img_h2, img_h1])

    cv.imwrite("/tmp/img_v.png", img_v)
    client.fput_object("processed", "final.png", "/tmp/img_v.png")

    return req
