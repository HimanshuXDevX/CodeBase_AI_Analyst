import logging
from typing import List

def get_repository_structure(repo, path: str = "", max_depth: int = 3, current_depth: int = 0) -> List[str]:
    if current_depth >= max_depth:
        return []
    structure = []
    try:
        contents = repo.get_contents(path)
        if not isinstance(contents, list):
            contents = [contents]
        for content in contents:
            if content.type == "dir":
                structure.append(f"📁 {content.path}/")
                structure.extend(get_repository_structure(repo, content.path, max_depth, current_depth + 1))
            else:
                size_kb = content.size / 1024
                structure.append(f"📄 {content.path} ({size_kb:.1f}KB)")
    except Exception as e:
        logger.warning(f"Error reading {path}: {str(e)}")
    return structure