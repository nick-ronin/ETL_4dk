import os
import pandas as pd
from datetime import datetime

def build_summary_text(filename, date, rows, mapper_result, quality, dedup, log_file_path):
    """
    Собирает полный текст отчёта: сверху сводка по качеству/дублям, снизу — лог обработки.
    Возвращает строку.
    """
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("ОТЧЁТ ОБ ОБРАБОТКЕ ФАЙЛА")
    summary_lines.append("=" * 60)
    summary_lines.append(f"Файл: {filename}")
    summary_lines.append(f"Дата обработки: {date}")
    summary_lines.append(f"Всего строк: {rows}")
    summary_lines.append("")

    # Валидация
    validation = mapper_result.get('validation_result', {})
    if validation.get('status') == 'WARNING':
        summary_lines.append(f"[!] Проблема: отсутствуют обязательные колонки: {validation.get('missing_columns', [])}")
    else:
        summary_lines.append("[OK] Все обязательные колонки присутствуют")
    summary_lines.append("")

    # Дубли
    rows_affected = dedup.get('rows_affected', 0)
    summary_lines.append(f"Дубликаты: затронуто строк – {rows_affected}")
    summary_lines.append("")

    # Качество
    summary_lines.append("КАЧЕСТВО ДАННЫХ:")
    for metric, value in quality['metrics'].items():
        summary_lines.append(f"  {metric}: {value}")
    summary_lines.append(f"  Общая оценка: {quality['overall_quality_score']}")
    summary_lines.append("")

    summary_lines.append("=" * 60)
    summary_lines.append("ПОДРОБНЫЙ ЛОГ ОБРАБОТКИ")
    summary_lines.append("=" * 60)

    # Читаем лог
    with open(log_file_path, 'r', encoding='utf-8') as f:
        log_content = f.read()

    return "\n".join(summary_lines) + "\n" + log_content


def save_report(report_text: str, output_folder: str = "output", base_name: str = "processing_report") -> dict:
    """Сохраняет переданный текст отчёта в .txt файл."""
    try:
        os.makedirs(output_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_folder, f"{base_name}_{timestamp}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return {'status': 'OK', 'file_path': file_path}
    except Exception as e:
        return {'status': 'ERROR', 'file_path': None, 'error': str(e)}


def save_data(df: pd.DataFrame, output_folder: str = "output", base_name: str = "cleaned_data") -> dict:
    """Сохраняет DataFrame в Excel."""
    try:
        os.makedirs(output_folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_folder, f"{base_name}_{timestamp}.xlsx")
        df.to_excel(file_path, index=False, engine='openpyxl')
        return {'status': 'OK', 'file_path': file_path}
    except Exception as e:
        return {'status': 'ERROR', 'file_path': None, 'error': str(e)}