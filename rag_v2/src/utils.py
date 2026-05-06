import random
from typing import List, Dict


def extract_answer(text: str) -> str:
    """从模型输出中提取答案（A/B/C/D）。

    优先级：[[A]] > [A] > 最后出现的 A/B/C/D
    """
    if "[[A]]" in text:
        return "A"
    elif "[[B]]" in text:
        return "B"
    elif "[[C]]" in text:
        return "C"
    elif "[[D]]" in text:
        return "D"
    elif "[A]" in text:
        return "A"
    elif "[B]" in text:
        return "B"
    elif "[C]" in text:
        return "C"
    elif "[D]" in text:
        return "D"
    else:
        for i in range(len(text) - 1, -1, -1):
            if text[i] == 'A':
                return "A"
            elif text[i] == 'B':
                return "B"
            elif text[i] == 'C':
                return "C"
            elif text[i] == 'D':
                return "D"
    return "A"


def most_common_element(lst: List[str]) -> str:
    """多数投票，返回出现最频繁的元素。"""
    element_freq = {}
    for item in lst:
        element_freq[item] = element_freq.get(item, 0) + 1
    most_common = max(element_freq, key=element_freq.get)
    return most_common


def shuffle_choices_4(choices: List[str]) -> tuple:
    """随机打乱 4 个选项，返回打乱后的列表和映射字典。

    Returns:
        (shuffled_choices, map_dict)
        map_dict: {"A": original_letter, "B": original_letter, ...}
    """
    shuffled = choices.copy()
    random.shuffle(shuffled)

    original = ["A", "B", "C", "D"]
    map_dict = {}

    for i, choice in enumerate(shuffled):
        for j, orig_choice in enumerate(choices):
            if choice == orig_choice:
                map_dict[original[i]] = original[j]
                break

    return shuffled, map_dict


def shuffle_choices_2(choices: List[str]) -> tuple:
    """随机打乱 2 个选项，返回打乱后的列表和映射字典。

    Returns:
        (shuffled_choices, map_dict)
        map_dict: {"A": original_letter, "B": original_letter}
    """
    shuffled = choices.copy()
    random.shuffle(shuffled)

    original = ["A", "B"]
    map_dict = {}

    for i, choice in enumerate(shuffled):
        for j, orig_choice in enumerate(choices):
            if choice == orig_choice:
                map_dict[original[i]] = original[j]
                break

    return shuffled, map_dict
