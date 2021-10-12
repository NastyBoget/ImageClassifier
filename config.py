import json
import os
from typing import Any


def check_key(config: dict, key: str, default_value: Any = None) -> None:
    if key not in config:
        if default_value is None:
            raise ValueError('{} is not set'.format(key))

        config[key] = default_value
        print('Warning: "{0}" is not set. Changed to "{1}"'.format(key, default_value))


def get_config(filename: str) -> dict:
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
