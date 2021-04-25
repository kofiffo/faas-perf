from PIL import Image
import base64


def handle(req):
    try:
        with open("image.png", 'wb') as file:
            file.write(base64.b64decode(req))

        img = Image.open("image.png")
        img = img.resize((img.width // 2, img.height // 2))
        resp = str(img.format) + ' ' + str(img.size) + ' ' + str(img.mode)
    except Exception as e:
        resp = str(e)

    return resp
