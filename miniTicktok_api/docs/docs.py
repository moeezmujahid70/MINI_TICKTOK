import glob
import ntpath
from pathlib import Path
from typing import List


def load_api_readme() -> str:
    path = Path(__file__).parent
    with open(f"{path}/api_readme.md", 'r') as file:
        description = file.read()

    return description


def load_api_tags() -> List:
    tags = []

    path = Path(__file__).parent
    tag_readme_paths = glob.glob(f"{path}/tags/*.md")

    for tag_readme_path in tag_readme_paths:
        with open(tag_readme_path, 'r') as file:
            tags.append({
                "name": ntpath.basename(tag_readme_path).split('.')[0],
                "description": file.read()
            })

    return tags
