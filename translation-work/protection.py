from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from errors import ProtectionError
from models import ProtectedText, ProtectedToken, TokenCategory

PROTECTION_REVISION = "soulash-protection-v2"
OPAQUE_TOKEN_RE = re.compile(r"__KEEP_\d+__")
COLOR_TAG_RE = re.compile(r"\[(/?)color(?:=[^\]]+)?\]", re.IGNORECASE)
ENGINE_TOKEN_RE = re.compile(r"::[A-Za-z_][A-Za-z0-9_]*")
BRACE_TOKEN_RE = re.compile(r"\{[^{}\r\n]*\}")
PRINTF_TOKEN_RE = re.compile(
    r"%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?"
    r"(?:hh|h|ll|l|j|z|t|L)?[diuoxXfFeEgGaAcspn%]"
)
NEWLINE_RE = re.compile(r"(?:\r\n|\n|\r)+")
COMPOUND_NUMBER_RE = re.compile(r"(?<!\w)(?:\d+d\d+|x\d+)(?!\w)", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![\w])[-+]?\d+(?:[.,]\d+)*(?:%?)(?![\w])")
PERCENT_RE = re.compile(r"%")
BUTTON_RE = re.compile(r"<<|>>|(?<![A-Za-z0-9])<|>(?![A-Za-z0-9])")


@dataclass(frozen=True, slots=True)
class _Span:
    start: int
    end: int
    raw: str
    token_type: str
    category: TokenCategory
    group: str | None = None
    role: str | None = None


def _collect_spans(text: str) -> list[_Span]:
    spans: list[_Span] = []
    tag_stack: list[str] = []
    group_index = 0
    for match in COLOR_TAG_RE.finditer(text):
        is_close = bool(match.group(1))
        if is_close:
            if not tag_stack:
                raise ProtectionError("Closing color tag has no matching opening tag")
            group = tag_stack.pop()
            role = "close"
        else:
            group = f"color-{group_index}"
            group_index += 1
            tag_stack.append(group)
            role = "open"
        spans.append(
            _Span(
                match.start(),
                match.end(),
                match.group(0),
                "color_tag",
                TokenCategory.PAIRED_STRUCTURAL,
                group,
                role,
            )
        )
    if tag_stack:
        raise ProtectionError("Opening color tag has no matching closing tag")

    patterns = (
        (ENGINE_TOKEN_RE, "engine_placeholder", TokenCategory.INDEPENDENT),
        (BRACE_TOKEN_RE, "format_placeholder", TokenCategory.INDEPENDENT),
        (PRINTF_TOKEN_RE, "printf_placeholder", TokenCategory.INDEPENDENT),
        (NEWLINE_RE, "line_break", TokenCategory.INDEPENDENT),
        (COMPOUND_NUMBER_RE, "numeric_expression", TokenCategory.INDEPENDENT),
        (BUTTON_RE, "control_glyph", TokenCategory.INDEPENDENT),
        (NUMBER_RE, "numeric_literal", TokenCategory.INDEPENDENT),
        (PERCENT_RE, "percent_symbol", TokenCategory.INDEPENDENT),
    )
    occupied = [(span.start, span.end) for span in spans]
    for pattern, token_type, category in patterns:
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied):
                continue
            spans.append(_Span(match.start(), match.end(), match.group(0), token_type, category))
            occupied.append((match.start(), match.end()))
    spans.sort(key=lambda span: (span.start, span.end))
    for previous, current in zip(spans, spans[1:], strict=False):
        if previous.end > current.start:
            raise ProtectionError("Overlapping protected syntax cannot be represented safely")
    return spans


def protect_text(text: str) -> ProtectedText:
    spans = _collect_spans(text)
    output: list[str] = []
    tokens: list[ProtectedToken] = []
    cursor = 0
    for index, span in enumerate(spans):
        placeholder = f"__KEEP_{index}__"
        output.append(text[cursor : span.start])
        output.append(placeholder)
        tokens.append(
            ProtectedToken(
                placeholder=placeholder,
                raw_value=span.raw,
                category=span.category,
                token_type=span.token_type,
                group=span.group,
                role=span.role,
            )
        )
        cursor = span.end
    output.append(text[cursor:])
    return ProtectedText("".join(output), tuple(tokens), PROTECTION_REVISION)


def _validate_structural_pairs(candidate: str, expected: tuple[ProtectedToken, ...]) -> None:
    by_placeholder = {token.placeholder: token for token in expected}
    stack: list[str] = []
    for placeholder in OPAQUE_TOKEN_RE.findall(candidate):
        token = by_placeholder.get(placeholder)
        if token is None or token.category is not TokenCategory.PAIRED_STRUCTURAL:
            continue
        if token.role == "open":
            if token.group is None:
                raise ProtectionError("Paired opening token is missing its structural group")
            stack.append(token.group)
        elif token.role == "close":
            if not stack or stack[-1] != token.group:
                raise ProtectionError("Paired markup is not balanced and properly nested")
            stack.pop()
    if stack:
        raise ProtectionError("Paired markup is not balanced and properly nested")


def validate_protected_translation(source: ProtectedText, candidate: str) -> None:
    expected_placeholders = Counter(token.placeholder for token in source.tokens)
    actual_placeholders = Counter(OPAQUE_TOKEN_RE.findall(candidate))
    if actual_placeholders != expected_placeholders:
        missing = expected_placeholders - actual_placeholders
        extra = actual_placeholders - expected_placeholders
        raise ProtectionError(
            f"Protected-token mismatch; missing={dict(missing)}, extra={dict(extra)}"
        )
    _validate_structural_pairs(candidate, source.tokens)
    without_placeholders = OPAQUE_TOKEN_RE.sub("", candidate)
    for token in source.tokens:
        if token.raw_value and token.raw_value in without_placeholders:
            raise ProtectionError(
                f"Raw protected value leaked instead of {token.placeholder}: {token.token_type}"
            )
    unauthorized_patterns = (
        ENGINE_TOKEN_RE,
        COLOR_TAG_RE,
        BRACE_TOKEN_RE,
        PRINTF_TOKEN_RE,
        NEWLINE_RE,
        COMPOUND_NUMBER_RE,
        NUMBER_RE,
        PERCENT_RE,
        BUTTON_RE,
    )
    if any(pattern.search(without_placeholders) for pattern in unauthorized_patterns):
        raise ProtectionError("Translation invented or leaked protected syntax")


def validate_restored_translation(source: ProtectedText, restored: str) -> None:
    restored_protected = protect_text(restored)
    expected_tokens = Counter((token.token_type, token.raw_value) for token in source.tokens)
    actual_tokens = Counter(
        (token.token_type, token.raw_value) for token in restored_protected.tokens
    )
    if expected_tokens != actual_tokens:
        missing = expected_tokens - actual_tokens
        extra = actual_tokens - expected_tokens
        raise ProtectionError(
            f"Restored technical-token mismatch; missing={dict(missing)}, extra={dict(extra)}"
        )


def restore_text(source: ProtectedText, candidate: str) -> str:
    validate_protected_translation(source, candidate)
    restored = candidate
    for token in source.tokens:
        restored = restored.replace(token.placeholder, token.raw_value)
    if OPAQUE_TOKEN_RE.search(restored):
        raise ProtectionError("Unknown opaque token remained after restoration")
    validate_restored_translation(source, restored)
    return restored
