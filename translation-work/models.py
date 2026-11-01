from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

JsonValue: TypeAlias = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
JsonPointer: TypeAlias = tuple[str | int, ...]


class TokenCategory(StrEnum):
    INDEPENDENT = "independent"
    PAIRED_STRUCTURAL = "paired_structural"
    GROUP_STRUCTURAL = "group_structural"
    FIXED_POSITION = "fixed_position"


@dataclass(frozen=True, slots=True)
class ProtectedToken:
    placeholder: str
    raw_value: str
    category: TokenCategory
    token_type: str
    group: str | None = None
    role: str | None = None


@dataclass(frozen=True, slots=True)
class ProtectedText:
    text: str
    tokens: tuple[ProtectedToken, ...]
    revision: str


@dataclass(frozen=True, slots=True)
class TranslationUnit:
    unit_id: str
    relative_path: str
    pointer: JsonPointer
    stable_path: str
    source_text: str
    protected: ProtectedText
    context: str
    output_pointer: JsonPointer | None = None
    synthetic: bool = False
    gender_eligible: bool = False

    @property
    def destination_pointer(self) -> JsonPointer:
        return self.output_pointer or self.pointer


@dataclass(slots=True)
class ParsedFile:
    relative_path: str
    source_path: Path
    kind: str
    data: JsonValue | None = None
    raw_bytes: bytes | None = None


@dataclass(slots=True)
class SourceProject:
    root: Path
    files: dict[str, ParsedFile]
    units: list[TranslationUnit]
    manifest_hash: str


@dataclass(frozen=True, slots=True)
class AcceptedTranslation:
    unit_id: str
    protected_text: str
    restored_text: str
    grammatical_gender: str | None = None


@dataclass(slots=True)
class ReconstructionResult:
    root: Path
    file_count: int
    unit_count: int
    manifest: dict[str, Any] = field(default_factory=dict)


