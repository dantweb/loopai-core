import csv
import json
import logging
import os
import re
from typing import Tuple, Iterable, Hashable, Dict, List, Union, Optional, Any

from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

import pandas as pd
from pandas import Series

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.services.session import session_id

logger = LoggerService()

class CsvAdapter(FileAdapterInterface):
    def __init__(self, file_path: str, fields: list, mapping: dict) -> None:
        super().__init__()
        self.separator: str = ';'
        self.file_path: str = file_path
        self.fields: list = fields
        self.mapping: dict = mapping

    # Public Methods
    def read(self, step_id: str, *args: str) -> list[dict[str, Any]]:
        path: str = self.get_full_path(self.file_path)
        logger.info('[CsvAdapter::read] Reading CSV file' + path)
        df: pd.DataFrame = pd.read_csv(path, sep=self.separator)
        logger.info('[CsvAdapter::read] Finished reading CSV file')
        data_list: List[Dict[str, Any]] = df.to_dict(orient='records')
        logger.info(f'[CsvAdapter::read] Converted DataFrame to list of dicts: {data_list}')
        return data_list

    def write(self, step_id: str, data: BroadcastData) -> bool:
        logger.info(f"[CsvAdapter::write] data type of : {type(data)}")
        data_to_write: Optional[Union[List[Dict[str, str]], Dict[str, str]]] = data.get('result').get('response')

        logger.info(f"[CsvAdapter::write] data type of 'data_to_write': {type(data_to_write)}")

        if not data_to_write:
            logger.warning("[CsvAdapter::write] No data to write; data is empty.")
            return False

        if not isinstance(data_to_write, (list, dict)):
            try:
                logger.error(f"[CsvAdapter::write] data in not list or dict. Trying to convert")
                data_to_write = json.loads(data_to_write)
            except json.JSONDecodeError as e:

                logger.error(f"[CsvAdapter::write] Error parsing JSON data: {e}")
                ValueError("Result response must be a list or a dict")
                return False

        path: str = self._prepare_file_path()

        try:
            with open(path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer: csv.DictWriter = csv.DictWriter(csvfile, fieldnames=self.fields, delimiter=self.separator)

                if self.fields:
                    self._write_header_if_needed(csvfile, writer)

                logger.info(f"[CsvAdapter::write] Want to write data: \n\n {data_to_write} \n\n -- end of data --")
                logger.info(f"[CsvAdapter::write] There are fields defined  : {self.fields}")
                logger.info(f"[CsvAdapter::write] There are mappings defined  : {self.mapping}")
                if isinstance(data_to_write, list):
                    self._write_list_data(writer, data_to_write, self.fields, self.mapping)
                elif isinstance(data_to_write, dict):
                    self._write_dict_data(writer, data_to_write, self.fields)

        except Exception as e:
            self._handle_write_exception(e)

        logger.info("Finished write operation")
        logging.debug("Finished write operation")
        return True

    # Private Methods
    def _prepare_file_path(self) -> str:
        path: str = self.get_full_path(self.file_path)
        logger.info('[CsvAdapter::write] Writing to CSV file: ' + path)

        if os.path.exists(path):
            path = self.get_new_filename(path)
            logger.info(f"[CsvAdapter::write] New filename will be used for writing the file : {path}")

        directory: str = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created new directory for writing: {directory}")

        return path

    def _write_list_data(self,
                         writer: csv.DictWriter,
                         data_to_write: List[Dict[str, str]],
                         fieldnames: List[str],
                         field_mapping: Dict[str, str])-> None:
        logger.info(f"[CsvAdapter::_write_list_data] Want to write in total: {len(data_to_write)} rows to CSV")
        logger.info(f"[CsvAdapter::_write_list_data] Data to write : {data_to_write} \n\n")
        for i, item in enumerate(data_to_write):
            logger.info(f'Writing row {i}: {item}')
            logger.info(f'Writing row {i}: datatype {type(item)}')
            writer.writerow(item)
            logger.info(f'Wrote row {i}: {item}')

    def _write_dict_data(self, writer: csv.DictWriter, data_to_write: Dict[str, str], fieldnames: List[str]) -> None:
        row_data: Dict[str, str] = {}
        for field in fieldnames:
            value: str = data_to_write.get(field, '(empty)')  # Default to '(empty)' if key is not found
            row_data[field] = self.clean_text(value)

        logging.debug(f"\n\nConstructed row: {row_data}")

        writer.writerow(row_data)
        logger.info(f'Wrote row: {row_data}')

    @staticmethod
    def _write_header_if_needed(csvfile, writer: csv.DictWriter) -> None:
        logger.info("Writing header if needed")
        if csvfile.tell() == 0:
            writer.writeheader()

    @staticmethod
    def _handle_write_exception(e: Exception) -> None:
        msg: str = f"An error occurred while writing to CSV: {e}"
        logger.error(msg)
        logging.error(msg)
        raise

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove or replace problematic characters
        if isinstance(text, str):
            text = re.sub(r'";\n\r,', ' ', text)  # Replace quotes, newlines, and commas with spaces
            text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)  # Remove control characters
            text = text.strip()  # Remove leading/trailing whitespace
        return text