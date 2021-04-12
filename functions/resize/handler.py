from PIL import Image

def handle(req):
    try:
        img = Image.frombytes("RGBA", (767, 769), bytes(req, "utf-8"))
        img = img.resize((img.width//2, img.height//2))
        resp = str(img.format) + ' ' + str(img.size) + ' ' + str(img.mode)
    except Exception as e:
        resp = str(e)

    return resp
