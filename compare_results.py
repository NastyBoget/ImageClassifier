import json
import os
import shutil
import sys
from typing import Tuple

from image_maker import get_paired_picture


def collect_statistics(labels1: dict, labels2: dict, task_dir: str) -> Tuple[dict, dict]:
    with open(os.path.join(task_dir, "tasks.json")) as f:
        tasks = json.load(f)
    bbox2img = {}
    for task in tasks.values():
        for line in task['data']:
            bbox2img[line['uid']] = line

    results = {"missed": [], "added": [], "correct": [], "mismatch": []}
    for key, value1 in labels1.items():
        if key not in labels2:
            results["missed"].append([key, value1["labeled"][0]])
            continue
        value2 = labels2[key]
        if value1["labeled"][0] == value2["labeled"][0]:
            results["correct"].append([key, value1["labeled"][0]])
        else:
            results["mismatch"].append([key, value1["labeled"][0], value2["labeled"][0]])
        del labels2[key]

    for key, value in labels2.items():
        results["added"].append([key, value["labeled"][0]])
    return results, bbox2img


def print_results(results: dict) -> None:
    correct, mismatch = len(results["correct"]), len(results["mismatch"])
    added, missed = len(results["added"]), len(results["missed"])
    precision = correct / (correct + added + mismatch)
    recall = correct / (correct + missed + mismatch)
    f_measure = 2 * precision * recall / (precision + recall)

    print(f"correct = {correct}, mismatch = {mismatch}, added = {added}, missed = {missed}")
    print(f"precision = {precision}")
    print(f"recall = {recall}")
    print(f"f_measure = {f_measure}")


def draw_errors(bbox2img: dict, results: dict, task_dir: str, out_dir: str) -> None:
    for key in ["added", "missed", "mismatch"]:
        errors_list = results[key]
        for error in errors_list:
            bboxes = error[0].split('___')[1:]
            if bboxes[0] not in bbox2img or bboxes[1] not in bbox2img:
                print(f"{error[0]} not found")
                continue
            bbox1 = bbox2img[bboxes[0]]
            bbox2 = bbox2img[bboxes[1]]

            if key == "mismatch":
                text = f"{key}: {error[1]} -> {error[2]}"
            else:
                text = f"{key}: {error[1]}"
            get_paired_picture(img_name1=os.path.join(task_dir, "images", bbox1['img_name']),
                               img_name2=os.path.join(task_dir, "images", bbox2['img_name']),
                               bbox1=bbox1['bbox'], bbox2=bbox2['bbox'],
                               out_dir=out_dir, text=text)


if __name__ == "__main__":
    args = sys.argv[1:]
    # python3 compare_results.py ~/Downloads/results_nasty ~/Downloads/results_ilya ~/work/multilingual_dataset/legal_russian/img_pair_classifier_395348 ~/Downloads/errors
    if len(args) != 4:
        print("You should provide 4 arguments: first_res_dir second_res_dir img_pair_classifier_tasks out_dir")
        exit(0)
    first_res_dir, second_res_dir, img_pair_classifier_tasks, out_dir = args[0], args[1], args[2], args[3]

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    # names like img_pair_classifier_000000_bE9.json
    first_res_list = [f for f in os.listdir(first_res_dir) if f.endswith(".json")]
    second_res_list = [f for f in os.listdir(second_res_dir) if f.endswith(".json")]
    results = {"missed": [], "added": [], "correct": [], "mismatch": []}

    for filename in first_res_list:
        print(filename)
        if filename not in second_res_list:
            print(f"{filename} not in {second_res_list} directory")
            continue
        with open(os.path.join(first_res_dir, filename)) as f_1, open(os.path.join(second_res_dir, filename)) as f_2:
            labels1 = json.load(f_1)
            labels2 = json.load(f_2)

        # img_pair_classifier_000000_bE9.json -> task_000000_bE9
        task_dir = os.path.join(img_pair_classifier_tasks,
                                f"task_{filename[len('img_pair_classifier_'):-len('.json')]}")

        local_results, bbox2img = collect_statistics(labels1, labels2, task_dir)
        for key, value in local_results.items():
            results[key].extend(value)
        draw_errors(bbox2img, local_results, task_dir, out_dir)
    print_results(results)
