# ImageClassifier for comparing lines in documents
Implementation of images classifier in JS and Flask

## How to start labeling
* Move your documents to ```docs``` directory, images of document pages to ```docs/images```
* Fill file with task (format description down)
* Change ```config.json``` (change labels, image_key, default_label_key and etc options)
* Open terminal and run ```python app.py```
* Go to ```localhost:port```, where port is described in config.json

## How to label
Click on button(s) and then click to ```save``` button or use short ```keys 1-9``` for first labels and press ```Enter```

## How to reset current labeling
Press button ```reset``` or ```0 key```

## How to get result
Result tasks saved to ```output_path``` output path defined in ```config.json```. All task from ```input_path``` copied to ```output_path``` with one addition key — ```result_key```

## Config example
```json
{
  "title": "Some title",
  "port": 5000,
  "debug": false,
  "labels": [
    { "label": "equal", "color": "#f00" },
    { "label": "greater", "color": "#0f0" },
    { "label": "less", "color": "#00f" },
    { "label": "other", "color": "#ff0" }
  ],
  "multiclass": true,
  "input_path": "tasks.json",
  "image_key": ["task_path"],
  "default_label_key": ["data", "bbox", "label"],
  "task_instruction_key": ["instruction"],
  "result_key": "labeled",
  "output_path": "labeled_tasks.json",
  "instruction": "Type some <b>hypertext</b> for label experts!",
  "templates_dir": "examples",
  "confirm_required": false,
  "sampling": "sequential"
}
```
## Config format
`title` — title of page

```port``` — port of Flask application

```debug``` — debug mode of Flask

```labels``` — dictionary of labels with colors

```multiclass``` — available more than one label

```input_path``` — file with tasks

```image_key``` — key for get path to image in tasks file (list of sequential keys)

```default_label_key``` — key for get default label (list of sequential keys)

```task_instruction_key``` — key for get instruction for task (list of sequential keys)

```result_key``` — key for saving results

```output_path``` — path to file with output tasks

```instruction``` — html content with instruction

```templates_dir``` — not used now

```confirm_required``` — require confirmation for save or not

```sampling``` — sampling mode for getting task (`random` or `sequential`)

## Labels item format
* label — name of class (not HTML)
* color — border and text color while button is pressed
* html — (optional) html content for button, for example icon: ```"html": "<span class='fa fa-header'></span> header"```

## Colors format of labels
* hex format — ```#ff00ff```
* rgb format — ```rgb(255, 0, 0)```
* hsl format — ```hsl(70, 80%, 50%)```

## Format of tasks.json
```json
{
  "task_id": {
    "doc_name": "doc_path",
    "data": [
      {
        "img_name": "name of page image",
        "line_uid": "unique identifier of the line",
        "bbox": {"left": 0, "top": 0, "width": 0, "height": 0}
      }
    ]
  }
}
```

## Example of tasks.json
```"image_key": ["task_path"]``` — image getting by only one key — tasks[task_id]["task_path"]

```"default_label_key": ["data", "bbox", "label"]``` — default label getting by three keys — tasks[task_id]["data"]["bbox"]["label"]

```json
{
  "0": {
    "doc_name": "doc1.pdf",
    "data": [
      {
        "img_name": "doc1_0001.jpeg",
        "line_num": 0,
        "line_uid": "",
        "text": "",
        "bbox": {"left": 0, "top": 0, "width": 0, "height": 0},
        "page_num": 0
      },
      {
        "img_name": "doc1_0001.jpeg",
        "line_num": 1,
        "line_uid": "",
        "text": "",
        "bbox": {"left": 1, "top": 1, "width": 1, "height": 1},
        "page_num": 0
      }
    ]
  },
  "1": {
    "doc_name": "doc2.pdf",
    "data": [
      {
        "img_name": "doc2_0001.jpeg",
        "line_num": 0,
        "line_uid": "",
        "text": "",
        "bbox": {"left": 0, "top": 0, "width": 0, "height": 0},
        "page_num": 0
      },
      {
        "img_name": "doc2_0002.jpeg",
        "line_num": 1,
        "line_uid": "",
        "text": "",
        "bbox": {"left": 0, "top": 0, "width": 0, "height": 0},
        "page_num": 1
      }
    ]
  }
}
```

## Instruction for tasks
Add to config key `task_instruction_key` with path to tasks instruction key, for example, `task_instruction_key: ["instruction"]`
