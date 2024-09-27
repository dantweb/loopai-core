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
        return df

    def write(self, step_id: str, result: str) -> bool:
        path = self.get_full_path(self.file_path)
        if os.path.exists(path):
            path = self.get_new_filename(path)
            logger = LoggerService()
            logger.info(f"[CsvAdapter::write] New filename used for writing: {path}")

        directory = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger_service.info(f"Created new directory for writing: {directory}")

        try:
            with open(path, mode=self.file_mode, newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'TITLE']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=self.separator)
                if csvfile.tell() == 0:
                    writer.writeheader()

                for i, item in enumerate(result['result']):
                    title = item.get('title', '').replace('"', '""')
                    body = item.get('body', '').replace('"', '""')
                    url = item.get('url', '').replace('"', '""')
                    pattern = re.compile(r"[^a-zA-Z0-9\s-]")
                    cleaned_content = pattern.sub('', body).replace('\n', '').replace('\r', '')
                    result_string = f'TITLE {title} BODY: {cleaned_content} URL: {url}'

        # Replace all matched characters with an empty string and remove newlines
                    writer.writerow({'ID': f"RR00{i}", 'TITLE': result_string})
                    logging.debug(f"Wrote row {i}: {result_string}")
                    self.logger_service.info(f'Wrote row {i}: {result_string}')

        except Exception as e:
            msg = f"An error occurred while writing to CSV: {e}"
            self.logger_service.error(msg)
            logging.error(msg)
            raise

        self.logger_service.info("Finished write operation")
        logging.debug("Finished write operation")
        return True
