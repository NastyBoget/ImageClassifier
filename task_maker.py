import os
from typing import List, Optional, Tuple

from image_maker import get_paired_picture


class TaskMaker:

    def __init__(self,
                 default_label: str,
                 instruction: str,
                 doc: dict,
                 completed_tasks: dict):
        self.default_label = default_label
        self.instruction = instruction
        self.doc = doc
        self.doc_name = doc["doc_name"]
        self.lines_num = len(doc["data"])
        self.completed_tasks = completed_tasks
        self.completed_task_ids_for_doc = [c_task_id for c_task_id in completed_tasks
                                           if c_task_id.startswith(self.doc_name)]

    def get_next_task(self) -> Optional[tuple]:
        # TODO order dict
        # consider first pair for current document
        if len(self.completed_task_ids_for_doc) == 0:
            return self.__make_one_task(line1=self.doc["data"][0], line2=self.doc["data"][1])
        # find last comparison for document
        last_line_uid, last_task_label = self.__get_last_info()
        current_line_id = self.__find_line(self.doc["data"], last_line_uid)

        if last_task_label == "other":
            first_line_id = self.__find_line_for_comparison(prev_label="other")
            if first_line_id is not None:
                return self.__get_next_task(first_line_id, current_line_id)

        if last_task_label == "greater":
            first_line_id = self.__find_line_for_comparison(prev_label="greater")
            if first_line_id is not None:
                return self.__make_one_task(line1=self.doc["data"][first_line_id],
                                            line2=self.doc["data"][current_line_id])
        return self.__get_next_task(current_line_id, current_line_id)

    def __get_next_task(self, first_line_id: int, second_line_id : int):
        if second_line_id < self.lines_num - 1:
            return self.__make_one_task(line1=self.doc["data"][first_line_id],
                                        line2=self.doc["data"][second_line_id + 1])
        else:
            return None

    def __get_last_info(self) -> Tuple[str, str]:
        last_task_id = self.completed_task_ids_for_doc[-1]
        last_task_label = self.completed_tasks[last_task_id]['labeled'][-1]
        last_line_uid = self.completed_task_ids_for_doc[-1].split('_')[-1]
        return last_line_uid, last_task_label

    def __find_line_for_comparison(self, prev_label: str) -> Optional[int]:
        if prev_label == "greater":
            # find the given line
            first_line_uid = self.completed_task_ids_for_doc[-1].split('_')[-2]
            # consider lines in reverse order
            for c_task_id in self.completed_task_ids_for_doc[::-1]:
                if c_task_id.endswith(first_line_uid):
                    new_first_line_uid = c_task_id.split('_')[-2]
                    if self.completed_tasks[c_task_id]["labeled"][-1] == "less":
                        return self.__find_line(self.doc["data"], new_first_line_uid)
                    first_line_uid = new_first_line_uid
            return None
        elif prev_label == "other":
            for c_task_id in self.completed_task_ids_for_doc[::-1]:
                if self.completed_tasks[c_task_id]["labeled"][-1] != "other":
                    new_first_line_uid = c_task_id.split('_')[-1]
                    return self.__find_line(self.doc["data"], new_first_line_uid)
            return None

    def __find_line(self, lines: List[dict], line_uid: str) -> Optional[int]:
        for i, line in enumerate(lines):
            if line["line_uid"] == line_uid:
                return i

    def __make_one_task(self, line1: dict, line2: dict) -> tuple:
        task_id = "{}_{}_{}".format(self.doc_name, line1["line_uid"], line2["line_uid"])
        img_filename = get_paired_picture(os.path.join("docs/images", line1["img_name"]),  # TODO images dir
                                          os.path.join("docs/images", line2["img_name"]),
                                          line1["bbox"], line2["bbox"])
        return task_id, {"img": img_filename, "label": self.default_label, "instruction": self.instruction}
