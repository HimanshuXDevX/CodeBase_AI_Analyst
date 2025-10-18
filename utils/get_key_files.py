import logging
from typing import List

def get_key_files(repo) -> List[FileInfo]:
    extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.jsx', '.tsx', '.vue', '.cpp', '.c', '.rb', '.php', '.cs', '.swift', '.kt']
    key_files = []
    files_to_process = []
    
    try:
        contents = repo.get_contents("")
        while contents and len(files_to_process) < 50:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                try:
                    contents.extend(repo.get_contents(file_content.path))
                except Exception as e:
                    logger.warning(f"Could not access directory {file_content.path}: {str(e)}")
            else:
                if any(file_content.path.endswith(ext) for ext in extensions):
                    if file_content.size < 100000:
                        files_to_process.append(file_content)
        
        priority_patterns = [
            'main.', 'app.', 'index.', 'server.', 'api.',
            'config.', 'route', 'controller', 'model',
            'service', 'component', 'page', 'layout', 'middleware'
        ]
        
        def file_priority(file):
            path_lower = file.path.lower()
            for i, pattern in enumerate(priority_patterns):
                if pattern in path_lower:
                    return i
            return len(priority_patterns)
        
        files_to_process.sort(key=file_priority)
        
        for file_content in files_to_process[:15]:
            try:
                content = file_content.decoded_content.decode('utf-8')
                key_files.append(FileInfo(
                    path=file_content.path,
                    content=content[:2000],
                    size_kb=file_content.size / 1024
                ))
                logger.info(f"Analyzed file: {file_content.path}")
            except Exception as e:
                logger.warning(f"Could not read file {file_content.path}: {str(e)}")
            if len(key_files) >= 15:
                break
    except Exception as e:
        logger.error(f"Error getting key files: {str(e)}")
    
    return key_files