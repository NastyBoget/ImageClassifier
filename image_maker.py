import os
from copy import deepcopy

import PIL
import numpy as np
from PIL import ImageDraw, Image


def draw_rectangle(image: PIL.Image,
                   x_top_left: int, y_top_left: int,
                   width: int, height: int, color: tuple = (0, 0, 0)) -> PIL.Image:
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
    if r_img1.height != r_img2.height:
        r_img2 = r_img2.resize((r_img2.width * r_img1.height // r_img2.height, r_img1.height))
    paired_img = Image.fromarray(np.concatenate((np.array(r_img1), np.array(r_img2)), axis=1))
    img_name = "r_{}.png".format(os.path.splitext(os.path.basename(img_name1))[0])
    path = os.path.join("images", img_name)
    with open(path, "wb") as f:
        paired_img.save(fp=f, format="PNG")
    return path
