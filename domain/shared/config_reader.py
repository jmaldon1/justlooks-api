import yaml
import os


def read_config(fpath: str):
    with open(fpath, 'r') as f:
        return yaml.safe_load(f)