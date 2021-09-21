from PIL import Image
import pytesseract
import cv2 as cv
import numpy as np
import requests
import os


def handle(req):

    r = requests.get(req)

    img_array = np.array(bytearray(r.content), dtype=np.uint8)
    img = cv.imdecode(img_array, -1)

    filename = "/tmp/image.png"
    cv.imwrite(filename, img)

    text = pytesseract.image_to_string(Image.open(filename), lang="eng")
    os.remove(filename)

    return text
