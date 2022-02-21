import os
from typing import List, Optional, Tuple

from image_maker import get_paired_picture


class TaskMaker:

    def __init__(self,
                 default_label: str,
                 instruction: str,
                 doc: dict,
                 completed_tasks: dict,
                 config: dict):
        self.default_label = default_label
        self.instruction = instruction
        self.doc = doc
        self.doc_name = doc["doc_name"]
        self.lines_num = len(doc["data"])
        self.completed_tasks = completed_tasks
        self.completed_task_ids_for_doc = [c_task_id for c_task_id in completed_tasks
                                           if c_task_id.startswith(self.doc_name)]
        self.label2color = {item["label"]: item["color"] for item in config["labels"]}

    def get_next_task(self) -> Optional[tuple]:
        # TODO order dict
        # consider first pair for current document
        if len(self.completed_task_ids_for_doc) == 0:
            return self.__make_one_task(line1=self.doc["data"][0], line2=self.doc["data"][1])
        # find last comparison for document
        last_uid, last_task_label = self.__get_last_info()
        current_line_id = self.__find_line(self.doc["data"], last_uid)

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
        last_uid = self.completed_task_ids_for_doc[-1].split('___')[-1]
        return last_uid, last_task_label

    def __find_line_for_comparison(self, prev_label: str) -> Optional[int]:
        if prev_label == "greater":
            # find the given line
            first_uid = self.completed_task_ids_for_doc[-1].split('___')[-2]
            # consider lines in reverse order
            for c_task_id in self.completed_task_ids_for_doc[::-1]:
                if c_task_id.endswith(first_uid):
                    new_first_uid = c_task_id.split('___')[-2]
                    if self.completed_tasks[c_task_id]["labeled"][-1] == "less":
                        return self.__find_line(self.doc["data"], new_first_uid)
                    first_uid = new_first_uid
            return None
        elif prev_label == "other":
            for c_task_id in self.completed_task_ids_for_doc[::-1]:
                if self.completed_tasks[c_task_id]["labeled"][-1] != "other":
                    new_first_uid = c_task_id.split('___')[-1]
                    return self.__find_line(self.doc["data"], new_first_uid)
            return None

    def __find_line(self, lines: List[dict], uid: str) -> Optional[int]:
        for i, line in enumerate(lines):
            if line["uid"] == uid:
                return i

    def __make_one_task(self, line1: dict, line2: dict) -> tuple:
        if "label" in line1 and "label" in line2:
            label = self._pair2label(line1["label"], line2["label"])
        else:
            label = self.default_label
        task_id = "{}___{}___{}".format(self.doc_name, line1["uid"], line2["uid"])

        color1 = self.label2color.get(label, (255, 0, 0))
        color2 = self.label2color.get(label, (0, 0, 255))
        img_filename = get_paired_picture(os.path.join("images", line1["img_name"]),  # TODO images dir
                                          os.path.join("images", line2["img_name"]),
                                          line1["bbox"], line2["bbox"], color1=color1, color2=color2)
        return task_id, {"img": img_filename, "label": label, "instruction": self.instruction}

    def _pair2label(self, first_label: str, second_label: str) -> str:
        """
        compares the levels of two lines, if the second line is less, greater or equal to the first one
        Parameters
        ----------
        first_label: str label with the first line level, e.g. "1"; the less level is, the more important the line is
        second_label: str the same label for the second line
        Returns comparative label: equal, less or greater
        -------
        """
        try:
            l1, l2 = int(first_label), int(second_label)
            if l1 > l2:
                return "greater"
            if l1 < l2:
                return "less"
            return "equal"
        except ValueError:
            return self.default_label
