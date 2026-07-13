import os
from pathlib import Path
from typing import Optional

def rotate_files(directory: str, max_files: int, reserved: Optional[list] = None):
    """
    Удаляет самые старые файлы в directory, если их количество превышает max_files.
    reserved — список имён файлов, которые нельзя удалять (например, ['app.log']).
    """
    if not os.path.isdir(directory):
        return
    
    # Получаем все файлы, сортируем по времени последнего изменения (старые первыми)
    files = [f for f in Path(directory).iterdir() if f.is_file()]
    files.sort(key=lambda f: f.stat().st_mtime)
    
    # Исключаем зарезервированные файлы из списка на удаление
    if reserved:
        reserved_set = set(reserved)
        deletable = [f for f in files if f.name not in reserved_set]
    else:
        deletable = files
    
    # Удаляем старейшие файлы, пока количество не станет <= max_files
    while len(deletable) > max_files:
        file_to_delete = deletable.pop(0)
        try:
            file_to_delete.unlink()
        except OSError as e:
            # Логировать ошибку при необходимости
            pass