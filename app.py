import os
import os.path
import json
import hashlib
import uuid
from typing import Optional, List

from flask import Flask
from flask import request, redirect, send_from_directory
from copy import deepcopy
import PIL
from PIL import Image, ImageDraw
import numpy as np

app = Flask(__name__)


def draw_rectangle(image: PIL.Image,
                   x_top_left: int,
                   y_top_left: int,
                   width: int,
                   height: int,
                   color: tuple = (0, 0, 0)) -> PIL.Image:
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
        r_img1 = draw_rectangle(img1, bbox1["left"], bbox1["top"], bbox1["width"], bbox1["height"], color=(255, 0, 0))
    with Image.open(img_name2) as img2:
        r_img2 = draw_rectangle(img2, bbox2["left"], bbox2["top"], bbox2["width"], bbox2["height"], color=(0, 0, 255))
    if r_img1.height != r_img2.height:
        r_img2 = r_img2.resize((r_img2.width * r_img1.height // r_img2.height, r_img1.height))
    paired_img = Image.fromarray(np.concatenate((np.array(r_img1), np.array(r_img2)), axis=1))
    img_name = "r_{}.png".format(os.path.splitext(os.path.basename(img_name1))[0])
    path = os.path.join("images", img_name)
    with open(path, "wb") as f:
        paired_img.save(fp=f, format="PNG")
    return path


@app.route('/<path:filename1>/<path:filename2>/<bbox1>/<bbox2>')
def image_file(filename1, filename2, bbox1, bbox2):
    # bbox = {"left", "top", "width", "height"}
    bbox1 = json.loads(bbox1)
    bbox2 = json.loads(bbox2)
    paired_filename = get_paired_picture(os.path.join("images", filename1),
                                         os.path.join("images", filename2), bbox1, bbox2)
    return send_from_directory(".", paired_filename)


@app.route('/js/<filename>')
def js_file(filename):
    return send_from_directory(app.config['JS_FOLDER'], filename)


@app.route('/css/<filename>')
def css_file(filename):
    return send_from_directory(app.config['CSS_FOLDER'], filename)


@app.route('/fonts/<filename>')
def font_file(filename):
    return send_from_directory(app.config['FONTS_FOLDER'], filename)


def get_by_key_list(task, keys):
    value = task

    for key in keys:
        value = value[key]

    return value


def read_next_task() -> Optional[tuple]:
    completed_tasks = get_completed_tasks()
    default_label = "equal"
    instruction = ""

    with open(os.path.abspath(config["input_path"]), "r", encoding='utf-8') as f:
        tasks = json.load(f)

    # consider all possible pairs, previous lines first in uid
    for doc_id, doc in tasks.items():
        lines_num = len(doc["data"])
        doc_name = doc["doc_name"]
        # consider first pair for current document
        if (not completed_tasks or not np.any(map(lambda x: x.startswith(doc_name), completed_tasks.keys()))) and lines_num > 1:  # TODO
            return make_one_task(doc_name=doc_name, line1=doc["data"][0], line2=doc["data"][1],
                                 default_label=default_label, instruction=instruction)

        # find last comparison for document
        # TODO order dict
        completed_task_ids_for_doc = [c_task_id for c_task_id in completed_tasks if c_task_id.startswith(doc_name)]
        last_task_id = completed_task_ids_for_doc[-1]
        last_task_label = completed_tasks[last_task_id]['labeled'][-1]
        last_line_uid = completed_task_ids_for_doc[-1].split('_')[-1]

        current_line_id = find_line(doc["data"], last_line_uid)
        if last_task_label == "equal" or last_task_label == "less":
            if current_line_id == lines_num - 1:
                continue
            return make_one_task(doc_name=doc_name,
                                 line1=doc["data"][current_line_id],
                                 line2=doc["data"][current_line_id + 1],
                                 default_label=default_label, instruction=instruction)
        elif last_task_label == "greater":
            # find the given line
            first_line_uid = completed_task_ids_for_doc[-1].split('_')[-2]
            # consider lines in reverse order
            for c_task_id in completed_task_ids_for_doc[::-1]:
                if c_task_id.endswith(first_line_uid):
                    new_first_line_uid = c_task_id.split('_')[-2]
                    if completed_tasks[c_task_id]["labeled"][-1] == "less":
                        new_first_line_id = find_line(doc["data"], new_first_line_uid)
                        return make_one_task(doc_name=doc_name,
                                             line1=doc["data"][new_first_line_id],
                                             line2=doc["data"][current_line_id],
                                             default_label=default_label, instruction=instruction)
                    first_line_uid = new_first_line_uid
            if current_line_id < lines_num - 1:
                return make_one_task(doc_name=doc_name,
                                     line1=doc["data"][current_line_id],
                                     line2=doc["data"][current_line_id + 1],
                                     default_label=default_label, instruction=instruction)
    return None


def find_line(lines: List[dict], line_uid: str) -> Optional[int]:
    for i, line in enumerate(lines):
        if line["line_uid"] == line_uid:
            return i


def make_one_task(doc_name: str, line1: dict, line2: dict, default_label: str, instruction: str) -> tuple:
    task_id = "{}_{}_{}".format(doc_name, line1["line_uid"], line2["line_uid"])
    return task_id, {"img": (line1["img_name"], line2["img_name"],
                             line1["bbox"], line2["bbox"]),
                     "label": default_label, "instruction": instruction}


def get_completed_tasks():
    with open(config["output_path"], 'r', encoding='utf-8') as f:
        completed_tasks = json.load(f)

    return completed_tasks


def get_md5(filename):
    with open(filename, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def save_completed_tasks(completed_tasks):
    with open(config["output_path"], 'w', encoding='utf-8') as f:
        json.dump(completed_tasks, f, indent=2, ensure_ascii=False)


def make_classifier(task_id, title, image, default_label, multiclass, task_instruction):
    labels = []
    image = "/{}/{}/{}/{}".format(os.path.join(image[0]), os.path.join(image[1]),
                                  json.dumps(image[2]), json.dumps(image[3]))

    for label_info in config["labels"]:
        label = label_info["label"]
        color = label_info.get("color", "")
        html = label_info.get("html", label)

        label_str = "label: \"" + label + "\""
        color_str = "" if color == "" else ", color: \"" + color + "\""
        html_str = "" if html == "" else ", html: \"" + html + "\""
        checked_str = ", checked: true" if label == default_label else ""
        labels.append("{" + label_str + color_str + checked_str + html_str + " }")

    completed_tasks = get_completed_tasks()
    labeled = "" if len(completed_tasks) == 0 else "<a href='/labeled'>Labeled tasks</a>"
    previous = "" if len(
        completed_tasks) == 0 else '''<div class='button' onclick='window.location.replace("/restore?task_id=''' + \
                                   list(completed_tasks.keys())[-1] + '''")'>Восстановить прошлую</div>'''

    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <link rel="stylesheet" type="text/css" href="css/styles.css?v={style}">
            <link rel="stylesheet" type="text/css" href="css/font-awesome.min.css">
        </head>
        <body>
            <div class="classifier">
                <div class="classifier-img" id="img">
                    <img src='{image}'>
                </div>

                <div class="classifier-controls">
                    <div class="classifier-buttons">
                        <div id="labels"></div>

                        <div class="button" onclick=classifier.Reset()>Сбросить</div>
                        <div class="button" onclick=classifier.Save()>Сохранить</div>
                        {previous}
                    </div>

                    <div class="text">
                        <b>Hot keys:</b><br>
                        <ul id="keys"></ul>
                    </div>
                </div>

                <div class="classifier-info">
                    <h2>Instruction</h2>
                    {instruction}
                </div>
            </div>

            <div>
                {labeled}
            </div>

            <script src="js/classifier.js?v={js}"></script>
            <script> 
                const MULTICLASS = {multiclass};
                const TASK_ID = '{task_id}';
                const REQUIRE_CONFIRMATION = {confirm_required};
                const LABELS = [
                    {labels}
                ]

                let classifier = new Classifier(LABELS)
            </script>
        </body>
        </html>
    '''.format(title=title,
               image=image,
               js=get_md5(app.config["JS_FOLDER"] + "/classifier.js"),
               style=get_md5(app.config["CSS_FOLDER"] + "/styles.css"),
               instruction=config["instruction"] + task_instruction,
               labeled=labeled,
               previous=previous,
               multiclass=("true" if multiclass else "false"),
               task_id=task_id,
               confirm_required=("true" if config["confirm_required"] else "false"),
               labels=",\n".join(labels))


def make_labeled(labeled_tasks):
    table = ''

    for task_id in labeled_tasks:
        task = labeled_tasks[task_id]
        img_name = get_by_key_list(task, config["image_key"])

        cells = "<td>" + str(task_id) + "</td>"
        cells += "<td><a target='_blank' href='" + img_name + "'>" + img_name + "</a></td>"
        cells += "<td>" + ",".join(task[config["result_key"]]) + "</td>"
        cells += "<td><a href='/restore?task_id=" + str(task_id) + "'>Restore</a></td>"
        table += "<tr>" + cells + "</tr>"

    return '''
    <!DOCTYPE html>
        <html>
        <head>
            <title>Labeled tasks</title>
            <link rel="stylesheet" type="text/css" href="css/styles.css?v={style}">
            <link rel="stylesheet" type="text/css" href="css/font-awesome.min.css">
        </head>
        <body>
            <table class='classifier-table'>
            <tr>
                <th>task_id</th>
                <th>image name</th>
                <th>labeled class(es)</th>
            </tr>
            {table}
            </table>
            <br>
            <a href="/">Go to label page</a>
        </body>
    </html>
    '''.format(
        style=get_md5(app.config["CSS_FOLDER"] + "/styles.css"),
        table=table
    )


@app.route('/', methods=['GET'])
def classify_image():
    available_task = read_next_task()

    if available_task is None:  # если их нет, то и размечать нечего
        return '''
        <p>Размечать нечего</p>
        <h1><a href="/get_results/{uid}">Результаты</a></h1>
        '''.format(uid=uuid.uuid1())

    task_id, task = available_task
    title = config["title"]
    return make_classifier(task_id, title, task["img"], task["label"], config["multiclass"],
                           task.get("instruction", ""))


@app.route('/save')
def save_file():
    task_id = request.args.get('task_id')
    labels = request.args.get('labels')

    completed_tasks = get_completed_tasks()
    completed_tasks[task_id] = {}  # добавляем выполненное задание
    completed_tasks[task_id][config["result_key"]] = labels.split(';')

    save_completed_tasks(completed_tasks)

    return redirect("/")  # возвращаем на страницу разметки


@app.route('/labeled')
def view_labeled():
    completed_tasks = get_completed_tasks()

    if len(completed_tasks) == 0:
        return "No tasks have been labeled, <a href='/'>go to label page</a>:"

    return make_labeled(completed_tasks)


@app.route('/restore')
def restore_task():
    task_id = request.args.get('task_id')
    completed_tasks = get_completed_tasks()
    del completed_tasks[task_id]

    save_completed_tasks(completed_tasks)

    return redirect(request.referrer)


@app.route('/get_results/<uid>')
def get_results(uid=None):
    result_file = config["output_path"]
    if not os.path.isfile(result_file):
        return "Nothing to download!"
    directory = os.path.dirname(result_file)
    filename = os.path.basename(result_file)
    return send_from_directory(directory, filename, as_attachment=True)


def check_key(config: dict, key: str, default_value=None):
    if key not in config:
        if default_value is None:
            raise ValueError('{} is not set'.format(key))

        config[key] = default_value
        print('Warning: "{0}" is not set. Changed to "{1}"'.format(key, default_value))


def get_config(filename: str):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        config = json.load(f)

    check_key(config, 'title', '')
    check_key(config, 'port', '5000')
    check_key(config, 'output_path', 'labeled_tasks.json')
    check_key(config, 'input_path', 'tasks.json')
    check_key(config, 'labels')
    check_key(config, 'multiclass', False)
    check_key(config, 'result_key', 'labeled')
    check_key(config, 'sampling', 'sequential')

    if config['sampling'] not in ['sequential', 'random', 'shuffle']:
        raise ValueError('Invalid "sampling" mode: {0}'.format(config['sampling']))

    for label in config['labels']:
        if 'label' not in label:
            raise ValueError('All labels must have "label" key')

    if len(set(label['label'] for label in config['labels'])) != len(config['labels']):
        raise ValueError('Labels are not unique')

    return config


if __name__ == '__main__':
    try:
        config = get_config('config.json')
        if os.path.isfile(os.path.abspath(config["intermediate_path"])):
            os.remove(os.path.abspath(config["intermediate_path"]))
        host = "0.0.0.0"
        port = config["port"]

        app.config['JS_FOLDER'] = 'js'  # папка с js кодом
        app.config['CSS_FOLDER'] = 'css'  # папка со стилями
        app.config['FONTS_FOLDER'] = 'fonts'  # папка со шрифтами

        if not os.path.exists(config["output_path"]):
            with open(config["output_path"], "w", encoding='utf-8') as f:
                f.write("{\n}")

        app.run(debug=config.get("debug", False), host=host, port=port)
    except ValueError as error:
        print(error)
