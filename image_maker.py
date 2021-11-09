import hashlib
import json
import os
from copy import deepcopy

from PIL import ImageDraw, Image

from config import get_config


def get_concat(im1: Image, im2: Image) -> Image:
    dst = Image.new('RGB', (im1.width + im2.width, max(im1.height, im2.height)))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


def draw_rectangle(image: Image,
                   x_top_left: int, y_top_left: int,
                   width: int, height: int, color: tuple = (0, 0, 0)) -> Image:
    if color == "black":
        color = (0, 0, 0)
    source_img = deepcopy(image).convert("RGBA")

    draw = ImageDraw.Draw(source_img)
    x_bottom_right = x_top_left + width + 5
    y_bottom_right = y_top_left + height + 5
    start_point = (x_top_left - 5, y_top_left - 5)
    end_point = (x_bottom_right, y_bottom_right)
    draw.rectangle((start_point, end_point), outline=color, width=5)
    return source_img


def get_paired_picture(img_name1: str, img_name2: str, bbox1: dict, bbox2: dict) -> str:
    # draw bbox1
    # draw bbox2
    # stack pictures
    with Image.open(img_name1) as img1:
        r_img1 = draw_rectangle(img1, bbox1["left"], bbox1["top"], bbox1["width"], bbox1["height"],
                                color=(255, 0, 0))
    with Image.open(img_name2) as img2:
        r_img2 = draw_rectangle(img2, bbox2["left"], bbox2["top"], bbox2["width"], bbox2["height"],
                                color=(0, 0, 255))
    paired_img = get_concat(r_img1, r_img2)
    hash_string = img_name1 + img_name2 + json.dumps(bbox1) + json.dumps(bbox2)
    img_name = "{}.png".format(hashlib.md5(hash_string.encode()).hexdigest())

    config = get_config('config.json')
    path = os.path.join(config["tmp_images_dir"], img_name)
    with open(path, "wb") as f:
        paired_img.save(fp=f, format="PNG")
    return img_name
