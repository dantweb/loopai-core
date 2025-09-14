import csv
import logging
import os
import re
from typing import Tuple, Iterable, Hashable, Dict, List, Union, Optional, Any, Set, Coroutine
from core.models.broadcast_data import BroadcastData
from core.services.logger_service import LoggerService

import pandas as pd
from pandas import Series

from core.adapters.file_adapter_interface import FileAdapterInterface

logger = LoggerService()

class CsvAdapter(FileAdapterInterface):
    def __init__(self, file_path: str, fields: list, mapping: dict) -> None:
        super().__init__()
        logger.info(f"[CsvAdapter::__init__] file_path: {file_path}")
        self.separator: str = ';'
        self.file_path: str = file_path
        self.fields: list = fields
        self.mapping: dict = mapping

    # Public Methods
    async def read(self, step_id: str, *args: str) -> BroadcastData:
        path: str = self.get_full_path(self.file_path)
        self.logger.info('[CsvAdapter::read] Reading CSV file' + path)
        df: pd.DataFrame = pd.read_csv(path, sep=self.separator)
        self.logger.info('[CsvAdapter::read] Finished reading CSV file')
        data_list: List[Dict[str, Any]] = df.to_dict(orient='records')
        self.logger.info(f'[CsvAdapter::read] Converted DataFrame to list of dicts: {data_list}')
        return BroadcastData({'list':data_list})

    async def write(self, step_id: str, data: BroadcastData) -> bool:
        self.logger.info(f"[CsvAdapter::write] data type of : {type(data)}")
        self.logger.info(f"[CsvAdapter::write] data : {str(data)}")

        # Extract the data dictionary from BroadcastData
        if hasattr(data, 'to_dict'):
            data_dict = data.to_dict()
        else:
            data_dict = data.__dict__

        extracted_data = self.extract_data_to_write(data_dict, self.fields)
        data_to_write = self.remove_duplicates(extracted_data)

        self.logger.info(f"[CsvAdapter::write] data type of 'data_to_write': {type(data_to_write)}")

        if not data_to_write:
            msg = "[CsvAdapter::write] No data was found with defined fields. Skipping CSV-adapter"
            self.logger.warning(msg)
            return False

        path: str = self._prepare_file_path()
        logger.info(f"[CsvAdapter::write] Writing to CSV file after _prepare_file_path: {path}")
        try:
            with open(path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fields, delimiter=self.separator)

                if self.fields:
                    self._write_header_if_needed(csvfile, writer)

                self.logger.info(f"[CsvAdapter::write] Writing data: \n\n {data_to_write} \n\n -- end of data --")
                if isinstance(data_to_write, list):
                    self._write_list_data(writer, data_to_write, self.fields, self.mapping)
                elif isinstance(data_to_write, dict):
                    self._write_dict_data(writer, data_to_write, self.fields)

        except Exception as e:
            self._handle_write_exception(e)

        self.logger.info("Finished write operation")
        return True

    # Private Methods
    def _prepare_file_path(self) -> str:
        path: str = self.get_full_path(self.file_path)
        self.logger.info('[CsvAdapter::write] Writing to CSV file: ' + path)

        directory: str = os.path.dirname(path)

        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created new directory for writing: {directory}")

        return path

    def _write_list_data(self,
                         writer: csv.DictWriter,
                         data_to_write: List[Dict[str, str]],
                         fieldnames: List[str],
                         field_mapping: Dict[str, str])-> None:
        self.logger.info(f"[CsvAdapter::_write_list_data] Want to write in total: {len(data_to_write)} rows to CSV")
        self.logger.info(f"[CsvAdapter::_write_list_data] Data to write : {data_to_write} \n\n")
        for i, item in enumerate(data_to_write):
            self.logger.info(f'Writing row {i}: {item}')
            self.logger.info(f'Writing row {i}: datatype {type(item)}')
            filtered_item = {key: value for key, value in item.items() if key in fieldnames}
            writer.writerow(filtered_item)
            self.logger.info(f'Wrote row {i}: {item}')

    def _write_dict_data(self, writer: csv.DictWriter, data_to_write: Dict[str, str], fieldnames: List[str]) -> None:
        row_data: Dict[str, str] = {}
        for field in fieldnames:
            value: str = data_to_write.get(field, '(empty)')  # Default to '(empty)' if key is not found
            row_data[field] = self.clean_text(value)

        logging.debug(f"\n\nConstructed row: {row_data}")

        writer.writerow(row_data)
        self.logger.info(f'Wrote row: {row_data}')

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


