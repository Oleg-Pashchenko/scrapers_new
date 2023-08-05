import requests


def download_image(link: str, index):
    filename = f"{index}.jpg"
    img_data = requests.get(link).content
    with open(filename, "wb") as handler:
        handler.write(img_data)
    handler.close()
    return filename

