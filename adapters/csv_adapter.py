import csv
import json
import logging
import os
import re
from typing import Tuple, Iterable, Hashable
from core.services.logger_service import LoggerService

import pandas as pd
from pandas import Series

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.session import session_id


class CsvAdapter(FileAdapterInterface):
    def __init__(self, file_path: str):
        super().__init__()
        self.separator = ';'
        self.file_path = file_path

    def read(self, step_id, *args) -> Iterable[tuple[Hashable, Series]]:
        path = self.get_full_path(self.file_path)
        logger = LoggerService()
        logger.info('[CsvAdapter::read] Reading CSV file' + path)
        df = pd.read_csv(path, sep=self.separator)
        logger.info('[CsvAdapter::read] Finished reading CSV file')
        return df

    def write(self, step_id: str, result: str) -> bool:
        fieldnames = json.loads(os.getenv('CSV_FIELDNAMES', '[]'))
        field_mapping = json.loads(os.getenv('CSV_FIELD_MAPPING', '{}'))

        if not fieldnames or not field_mapping:
            raise ValueError("Fieldnames or field mapping missing from environment variables")

        path = self.get_full_path(self.file_path)
        logger = LoggerService()
        logger.info('[CsvAdapter::write] Writing to CSV file: ' + json.dumps(result))

        if os.path.exists(path):
            path = self.get_new_filename(path)
            logger.info(f"[CsvAdapter::write] New filename used for writing: {path}")

        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created new directory for writing: {directory}")

        try:
            with open(path, mode=self.file_mode, newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.separator)

                if csvfile.tell() == 0:
                    writer.writeheader()

                for i, item in enumerate(result['result']):
                    self.logger_service.info(f'Writing row {i}: {item}')

                    row_data = {}
                    for field in fieldnames:
                        item_key = field_mapping.get(field)
                        value = item.get(item_key, '')  # Default to empty string if key is not found

                        row_data[field] = self.clean_text(value)

                    logging.debug(f"\n\nConstructed row {i}: {row_data}")

                    writer.writerow(row_data)
                    self.logger_service.info(f'Wrote row {i}: {row_data}')

        except Exception as e:
            msg = f"An error occurred while writing to CSV: {e}"
            self.logger_service.error(msg)
            logging.error(msg)
            raise

        self.logger_service.info("Finished write operation")
        logging.debug("Finished write operation")
        return True

    def clean_text(self, text: str) -> str:
        # Remove or replace problematic characters
        if isinstance(text, str):
            text = re.sub(r'[";\n\r,]', ' ', text)  # Replace quotes, newlines, and commas with spaces
            text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)  # Remove control characters
            text = text.strip()  # Remove leading/trailing whitespace
        return text