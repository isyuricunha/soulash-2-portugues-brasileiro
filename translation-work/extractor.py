from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from errors import FormatError, ProtectionError, ValidationError
from models import (
    AcceptedTranslation,
    JsonPointer,
    JsonValue,
    ParsedFile,
    ReconstructionResult,
    SourceProject,
    TranslationUnit,
)
from protection import (
    protect_text,
    restore_text,
    validate_protected_translation,
    validate_restored_translation,
)

SOURCE_SCHEMA_REVISION = "soulash-source-v2"
INCLUDED_DIRECTORIES = {"abilities", "buildings", "entities", "events", "milestones", "npc"}
INCLUDED_ROOT_FILES = {
    "ability_amplifiers.json",
    "ability_stackers.json",
    "building_groups.json",
    "building_names.json",
    "character.json",
    "conversations.json",
    "dialogues.json",
    "goals.json",
    "language_metadata.json",
    "locations.json",
    "messages.json",
    "passives.json",
    "region_names.json",
    "skills.json",
    "tutorial.json",
    "weather.json",
}
SCALAR_KEYS = {
    "affix",
    "ally_dialogue",
    "announcement",
    "answer_negative",
    "answer_positive",
    "begin",
    "death_text",
    "description",
    "dialogue",
    "end",
    "fail",
    "failure",
    "failure_message",
    "flavor",
    "format",
    "full_name",
    "history_event",
    "label",
    "long",
    "message",
    "monologue",
    "name",
    "objective",
    "orphan_surname",
    "rumor",
    "short",
    "success",
    "success_message",
    "text",
    "title",
    "trigger_message",
}
STRING_LIST_KEYS = {
    "ability_requirement",
    "ability_target",
    "ai_behaviors",
    "ally_dialogue",
    "aoe_shape",
    "attackNames",
    "beginning",
    "core_names",
    "crimes",
    "day_part",
    "desert",
    "formats",
    "hit_location",
    "item_type",
    "monologue",
    "names",
    "player_dialogue",
    "precipitations",
    "prefixes",
    "rarity",
    "rumors",
    "skill_levels",
    "suffixes",
    "tag",
    "temperatures",
    "weapon_type",
    "year_part",
}
GENDER_VALUES = {"masculine", "feminine"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _pointer_label(pointer: JsonPointer) -> str:
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in pointer)


def _get_pointer(root: JsonValue, pointer: JsonPointer) -> JsonValue:
    current: JsonValue = root
    for part in pointer:
        if (isinstance(part, int) and isinstance(current, list)) or (
            isinstance(part, str) and isinstance(current, dict)
        ):
            current = current[part]
        else:
            raise ValidationError(f"Invalid JSON pointer {_pointer_label(pointer)}")
    return current


def _set_pointer(root: JsonValue, pointer: JsonPointer, value: JsonValue) -> None:
    if not pointer:
        raise ValidationError("The JSON root cannot be replaced by a translation unit")
    parent = _get_pointer(root, pointer[:-1])
    leaf = pointer[-1]
    if (isinstance(leaf, int) and isinstance(parent, list)) or (
        isinstance(leaf, str) and isinstance(parent, dict)
    ):
        parent[leaf] = value
    else:
        raise ValidationError(f"Invalid destination pointer {_pointer_label(pointer)}")


def _delete_pointer(root: JsonValue, pointer: JsonPointer) -> None:
    if not pointer:
        raise ValidationError("The JSON root cannot be deleted")
    parent = _get_pointer(root, pointer[:-1])
    leaf = pointer[-1]
    if isinstance(leaf, int) and isinstance(parent, list):
        del parent[leaf]
    elif isinstance(leaf, str) and isinstance(parent, dict):
        if leaf not in parent:
            raise ValidationError(f"Missing destination pointer {_pointer_label(pointer)}")
        del parent[leaf]
    else:
        raise ValidationError(f"Invalid destination pointer {_pointer_label(pointer)}")


def _stable_list_segment(item: JsonValue, occurrence: int) -> str:
    if isinstance(item, dict) and isinstance(item.get("id"), (str, int)):
        return f"@id={item['id']}#{occurrence}"
    digest = _sha256_bytes(_canonical_json(item))[:16]
    return f"@value={digest}#{occurrence}"


class SoulashFormatHandler:
    def discover(self, root: Path) -> list[Path]:
        if not root.is_dir():
            raise FormatError(f"Source directory does not exist: {root}")
        discovered: list[Path] = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".txt"}:
                continue
            relative = path.relative_to(root)
            if len(relative.parts) == 1:
                if path.name in INCLUDED_ROOT_FILES:
                    discovered.append(path)
            elif relative.parts[0] in INCLUDED_DIRECTORIES:
                discovered.append(path)
        return sorted(discovered, key=lambda path: path.relative_to(root).as_posix().casefold())

    def load(self, root: Path) -> SourceProject:
        files: dict[str, ParsedFile] = {}
        units: list[TranslationUnit] = []
        manifest_entries: list[tuple[str, str]] = []
        for path in self.discover(root):
            relative_path = path.relative_to(root).as_posix()
            raw_bytes = path.read_bytes()
            manifest_entries.append((relative_path, _sha256_bytes(raw_bytes)))
            if path.suffix.lower() == ".txt":
                files[relative_path] = ParsedFile(
                    relative_path=relative_path,
                    source_path=path,
                    kind="txt",
                    raw_bytes=raw_bytes,
                )
                continue
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError as error:
                raise FormatError(f"JSON is not UTF-8: {path}") from error
            try:
                data = json.loads(text, object_pairs_hook=self._reject_duplicate_keys)
            except (json.JSONDecodeError, ValueError) as error:
                raise FormatError(f"Invalid JSON source {path}: {error}") from error
            files[relative_path] = ParsedFile(
                relative_path=relative_path,
                source_path=path,
                kind="json",
                data=data,
                raw_bytes=raw_bytes,
            )
            if relative_path != "language_metadata.json":
                units.extend(self._extract_file_units(relative_path, data))
        unit_ids = [unit.unit_id for unit in units]
        duplicates = [unit_id for unit_id, count in Counter(unit_ids).items() if count > 1]
        if duplicates:
            raise FormatError(f"Duplicate stable unit IDs: {duplicates[:5]}")
        manifest_hash = _sha256_bytes(_canonical_json(manifest_entries))
        return SourceProject(root=root, files=files, units=units, manifest_hash=manifest_hash)

    @staticmethod
    def _reject_duplicate_keys(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def _extract_file_units(self, relative_path: str, data: JsonValue) -> list[TranslationUnit]:
        units: list[TranslationUnit] = []

        def emit(
            source_text: str,
            pointer: JsonPointer,
            stable_parts: tuple[str, ...],
            context: str,
            *,
            output_pointer: JsonPointer | None = None,
            synthetic: bool = False,
            gender_eligible: bool = False,
        ) -> None:
            if not source_text.strip():
                return
            protected = protect_text(source_text)
            stable_path = "/".join(stable_parts)
            identity = f"{SOURCE_SCHEMA_REVISION}\0{relative_path}\0{stable_path}"
            unit_id = "s2-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            units.append(
                TranslationUnit(
                    unit_id=unit_id,
                    relative_path=relative_path,
                    pointer=pointer,
                    stable_path=stable_path,
                    source_text=source_text,
                    protected=protected,
                    context=context,
                    output_pointer=output_pointer,
                    synthetic=synthetic,
                    gender_eligible=gender_eligible,
                )
            )

        def walk(value: JsonValue, pointer: JsonPointer, stable_parts: tuple[str, ...]) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_pointer = pointer + (key,)
                    child_stable = stable_parts + (key,)
                    if isinstance(child, str) and self._is_scalar_translatable(
                        relative_path, key, pointer
                    ):
                        is_root_entity_name = relative_path.startswith(
                            "entities/"
                        ) and child_pointer == ("name",)
                        emit(
                            child,
                            child_pointer,
                            child_stable,
                            self._context(relative_path, child_pointer),
                            gender_eligible=is_root_entity_name,
                        )
                        if (
                            relative_path.startswith("entities/")
                            and child_pointer[-2:] == ("resource", "affix")
                            and child.strip()
                        ):
                            emit(
                                child,
                                child_pointer,
                                child_stable + ("@feminine",),
                                self._context(relative_path, child_pointer)
                                + "; translate as the feminine adjective form",
                                output_pointer=pointer + ("feminine_affix",),
                                synthetic=True,
                            )
                    elif isinstance(child, list) and key in STRING_LIST_KEYS:
                        self._walk_string_list(
                            child,
                            child_pointer,
                            child_stable,
                            relative_path,
                            emit,
                        )
                    else:
                        walk(child, child_pointer, child_stable)
            elif isinstance(value, list):
                occurrences: Counter[str] = Counter()
                for index, child in enumerate(value):
                    fingerprint = _sha256_bytes(_canonical_json(child))[:16]
                    if isinstance(child, dict) and isinstance(child.get("id"), (str, int)):
                        occurrence_key = f"id:{child['id']}"
                    else:
                        occurrence_key = f"value:{fingerprint}"
                    occurrence = occurrences[occurrence_key]
                    occurrences[occurrence_key] += 1
                    segment = _stable_list_segment(child, occurrence)
                    walk(child, pointer + (index,), stable_parts + (segment,))

        walk(data, (), ())
        return units

    @staticmethod
    def _walk_string_list(
        value: list[JsonValue],
        pointer: JsonPointer,
        stable_parts: tuple[str, ...],
        relative_path: str,
        emit: Any,
    ) -> None:
        occurrences: Counter[str] = Counter()

        def walk_list(
            items: list[JsonValue],
            current_pointer: JsonPointer,
            current_stable: tuple[str, ...],
        ) -> None:
            for index, item in enumerate(items):
                if isinstance(item, str):
                    digest = _sha256_bytes(item.encode("utf-8"))[:16]
                    occurrence = occurrences[digest]
                    occurrences[digest] += 1
                    emit(
                        item,
                        current_pointer + (index,),
                        current_stable + (f"@text={digest}#{occurrence}",),
                        SoulashFormatHandler._context(relative_path, current_pointer + (index,)),
                    )
                elif isinstance(item, list):
                    walk_list(
                        item,
                        current_pointer + (index,),
                        current_stable + (f"@list={index}",),
                    )

        walk_list(value, pointer, stable_parts)

    @staticmethod
    def _is_scalar_translatable(relative_path: str, key: str, parent: JsonPointer) -> bool:
        if relative_path == "messages.json":
            return key != "id"
        if relative_path == "dialogues.json" and key == "name":
            return False
        if key not in SCALAR_KEYS:
            return False
        if key == "affix":
            return relative_path.startswith("entities/") and parent[-1:] == ("resource",)
        return True

    @staticmethod
    def _context(relative_path: str, pointer: JsonPointer) -> str:
        section = relative_path.split("/", 1)[0]
        return f"Soulash 2 {section}; {relative_path} {_pointer_label(pointer)}"

