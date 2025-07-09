from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class InputConfig:
    csv: Dict[str, str] = None
    text: Dict[str, str] = None
    image: Dict[str, str] = None
    broadcast: Dict[str, str] = None
    source: Optional[str] = None
    output_format: Optional[str] = None
    field: Optional[str] = None
    filesystem: Dict[str, str] = None
    http: Dict[str, str] = None
    httprequest: Dict[str, str] = None
