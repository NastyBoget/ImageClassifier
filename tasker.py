# task example
# {
#     "0": {"doc_name": "doc1.pdf",
#           "data": [{"img_name": "doc1_0001.jpeg",
#                     "line_num": 0,
#                     "line_uid": "",
#                     "text": "",
#                     "bbox": {"left": 0, "top": 0, "width": 0, "height": 0},
#                     "page_num": 0},
#                    {"img_name": "doc1_0001.jpeg",
#                     "line_num": 1,
#                     "line_uid": "",
#                     "text": "",
#                     "bbox": {"left": 1, "top": 1, "width": 1, "height": 1},
#                     "page_num": 0}
#                     ]
#           },
#     "1": {"doc_name": "doc2.pdf",
#           "data": [{"img_name": "doc2_0001.jpeg",
#                     "line_num": 0,
#                     "line_uid": "",
#                     "text": "",
#                     "bbox": {"left": 0, "top": 0, "width": 0, "height": 0},
#                     "page_num": 0},
#                    {"img_name": "doc2_0002.jpeg",
#                     "line_num": 1,
#                     "line_uid": "",
#                     "text": "",
#                     "bbox": {"left": 1, "top": 1, "width": 1, "height": 1},
#                     "page_num": 1}
#                    ]
#           }
# }
import json
import os
from typing import List, Optional

import pdf2image as p2i
import pytesseract
from PIL import Image
from tqdm import tqdm


def is_box_in(box1: dict, box2: dict) -> bool:
    """
    check if box1 is in box2
    """
    x1, y1, w1, h1 = box1["left"], box1["top"], box1["width"], box1["height"]
    x2, y2, w2, h2 = box2["left"], box2["top"], box2["width"], box2["height"]
    return (x1 >= x2) and (y1 >= y2) and (x1 + w1 <= x2 + w2) and (y1 + h1 <= y2 + h2)


def pdf2imgs(path_in: str, path_out: str) -> Optional[List[str]]:
    if path_in.endswith('.pdf'):
        images = p2i.convert_from_path(path_in, fmt='JPEG')
        res = []
        for i, img in enumerate(images):
            img_name = "{}_{}.jpeg".format(os.path.splitext(os.path.basename(path_in))[0], i)
            img_path = os.path.join(path_out, img_name)
            res.append(img_name)
            with open(img_path, "wb") as f:
                img.save(fp=f, format="JPEG")
    else:
        print(path_in)
        return
    return res


def imgs2data(img_paths: List[str], doc_name: str, img_dir: str) -> dict:
    """
    :param img_paths: list of paths to pictures
    :param doc_name: path to document
    :param img_dir: directory with images
    :return: list of lines with bounding boxes
    bounding box: {"left", "top", "width", "height"}
    """
    result = {"doc_name": doc_name,
              "data": []}
    for img_num, img_path in tqdm(enumerate(img_paths)):
        with Image.open(os.path.join(img_dir, img_path)) as img:
            d = pytesseract.image_to_data(img, lang='rus+eng', output_type=pytesseract.Output.DICT)
        lines = []
        for i in range(len(d['level'])):
            if d['level'][i] == 4:  # bounding box of text line
                line_dict = {'img_name': os.path.basename(img_path),
                             'text': '',
                             'bbox': {"left": d['left'][i], "top": d['top'][i],
                                      "width": d['width'][i], "height": d['height'][i]}}
                lines.append(line_dict)
        for i in range(len(d['level'])):
            if d['level'][i] == 5:  # bounding box of some word
                box = {"left": d['left'][i], "top": d['top'][i], "width": d['width'][i], "height": d['height'][i]}
                for line_dict in lines:
                    if is_box_in(box, line_dict['bbox']):
                        if line_dict['text'] != '':
                            line_dict['text'] += ' '
                        line_dict['text'] += d['text'][i]
        for i, line_dict in enumerate(lines):
            line_dict["page_num"] = img_num
        result["data"].extend(lines)
    for i, line_dict in enumerate(result["data"]):
        line_dict["line_num"] = i
        line_dict["line_uid"] = str(i)
    return result


if __name__ == "__main__":
    paths = ["docs/doc1.pdf", "docs/doc2.pdf"]
    out_dir = "docs/images"
    os.makedirs(out_dir, exist_ok=True)
    tasks = {}
    for i, path in enumerate(paths):
        img_paths = pdf2imgs(path, out_dir)
        if img_paths:
            doc_dict = imgs2data(img_paths, path, out_dir)
            tasks[str(i)] = doc_dict
    with open("tasks.json", "w") as f:
        json.dump(tasks, f)
