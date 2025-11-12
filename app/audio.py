"""Utilities for discovering and preparing audio workbook assets."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import List, Sequence, Tuple

logger = logging.getLogger(__name__)


FILE_PATTERN = re.compile(
    r"^Thk2e_BE_L0_WB_Unit_(?P<unit>[A-Za-z0-9]+)_p(?P<page>\d+)_t(?P<test>\d+)\.mp3$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AudioResource:
    """Representation of a single workbook audio asset."""

    unit: str
    page: int
    page_display: str
    test_display: str
    relative_path: str

    @property
    def display_name(self) -> str:
        """Human readable label displayed in the UI."""

        return f"{self.unit}.{self.test_display}(p{self.page_display})"


def _unit_sort_key(unit: str) -> Tuple[int, int | str]:
    if unit.upper() == "W":
        return (0, 0)
    try:
        return (1, int(unit))
    except ValueError:
        return (2, unit.upper())


def _resource_sort_key(resource: AudioResource) -> Tuple[Tuple[int, int | str], int, int]:
    try:
        test_value = int(resource.test_display)
    except ValueError:
        test_value = 0
    return (_unit_sort_key(resource.unit), resource.page, test_value)


def load_audio_resources(audio_dir: Path) -> List[AudioResource]:
    """Scan ``audio_dir`` for workbook MP3 assets."""

    if not audio_dir.exists():
        logger.warning("Audio directory %s does not exist", audio_dir)
        return []

    resources: list[AudioResource] = []
    for file_path in sorted(audio_dir.rglob("*.mp3")):
        match = FILE_PATTERN.match(file_path.name)
        if not match:
            logger.debug("Skipping unexpected audio file pattern: %s", file_path.name)
            continue

        unit = match.group("unit").upper()
        page_raw = match.group("page")
        test_raw = match.group("test")
        try:
            page_number = int(page_raw)
        except ValueError:
            page_number = 0

        resources.append(
            AudioResource(
                unit=unit,
                page=page_number,
                page_display=page_raw,
                test_display=test_raw.zfill(2),
                relative_path=file_path.relative_to(audio_dir).as_posix(),
            )
        )

    resources.sort(key=_resource_sort_key)
    logger.info("Loaded %d audio resources from %s", len(resources), audio_dir)
    return resources


def group_audio_by_unit(resources: Sequence[AudioResource]) -> List[Tuple[str, List[AudioResource]]]:
    """Group resources by unit, preserving the desired presentation order."""

    grouped: dict[str, list[AudioResource]] = {}
    for resource in resources:
        grouped.setdefault(resource.unit, []).append(resource)

    ordered_units = sorted(grouped.keys(), key=_unit_sort_key)
    return [(unit, sorted(grouped[unit], key=_resource_sort_key)) for unit in ordered_units]


def first_n(resources: Sequence[AudioResource], count: int) -> List[AudioResource]:
    """Return up to ``count`` leading resources from the ordered collection."""

    return list(resources[:count])

