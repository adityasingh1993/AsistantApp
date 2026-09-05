"""
overlay/planner.py
Converts LLM free-text responses into structured overlay step dicts.

The planner:
  1. Parses numbered list items from the LLM response.
  2. For each step, tries to identify an action verb (click, fill, etc.)
     and a target widget name, then resolves it against the ManifestStore.
  3. Returns a list of step dicts that the AppAI SDK can render as overlays.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Action verbs used to trigger widget resolution
_RESOLVE_TRIGGERS = ["click", "tap", "open", "select", "find", "navigate to",
                     "fill", "enter", "type", "drag", "drop", "choose"]

# Regex that captures everything after a trigger keyword on the same fragment
_TRIGGER_RE = re.compile(
    r"(?:navigate to|click|tap|open|select|find|fill|enter|type|drag|drop|choose)\s+([\w\s]+)",
    re.IGNORECASE,
)

# Style assignment rules (checked in order)
_STYLE_RULES = [
    (re.compile(r"\b(click|tap)\b", re.I),           "pulse_ring"),
    (re.compile(r"\b(fill|enter|type)\b", re.I),     "glow_box"),
    (re.compile(r"\b(drag|drop)\b", re.I),           "drop_zone"),
    (re.compile(r"\b(select|choose)\b", re.I),       "highlight_box"),
]
_DEFAULT_STYLE = "pulse_ring"

# wait_for rules
_WAIT_FOR_RULES = [
    (re.compile(r"\b(fill|enter|type)\b", re.I),   "input"),
    (re.compile(r"\b(drag|drop)\b", re.I),          "drop"),
]
_DEFAULT_WAIT_FOR = "click"


def _assign_style(text: str) -> str:
    for pattern, style in _STYLE_RULES:
        if pattern.search(text):
            return style
    return _DEFAULT_STYLE


def _assign_wait_for(text: str) -> str:
    for pattern, wait in _WAIT_FOR_RULES:
        if pattern.search(text):
            return wait
    return _DEFAULT_WAIT_FOR


class OverlayPlanner:
    """
    Parses LLM responses and resolves UI overlay step dicts.

    Args:
        manifest_store: ManifestStore instance used for widget lookup.
    """

    def __init__(self, manifest_store):
        self._manifest = manifest_store

    # ── parsing ──────────────────────────────────────────────────────────────

    def parse_steps(self, llm_response_text: str) -> list[str]:
        """
        Extract numbered list items from the LLM response.

        Matches lines like:
          "1. Click the File menu"
          "2) Open the Export dialog"

        Returns a list of step strings (without the leading number).
        """
        steps = []
        # Match "1." or "1)" style numbering at the start of a line
        pattern = re.compile(r"^\s*\d+[.)]\s+(.+)$", re.MULTILINE)
        for match in pattern.finditer(llm_response_text):
            step_text = match.group(1).strip()
            if step_text:
                steps.append(step_text)
        return steps

    # ── widget resolution ────────────────────────────────────────────────────

    async def resolve_widget(self, app_id: str, step_text: str) -> Optional[str]:
        """
        Try to extract a widget label from the step text and look it up in
        the ManifestStore.

        Returns:
            widget_id string if found, else None.
        """
        match = _TRIGGER_RE.search(step_text)
        if not match:
            return None

        candidate_label = match.group(1).strip()
        # Remove trailing filler words
        candidate_label = re.sub(r"\b(the|a|an|to|and|or)\b", "", candidate_label, flags=re.I).strip()

        widget = await self._manifest.find_widget_by_label(app_id, candidate_label)
        if widget:
            return widget["widget_id"]
        return None

    # ── overlay step builder ─────────────────────────────────────────────────

    async def build_overlay_steps(
        self, app_id: str, llm_response_text: str
    ) -> list[dict]:
        """
        Full pipeline: parse steps → resolve widgets → return overlay dicts.

        Returns a list of overlay step dicts:
        {
            "step":      <int>,
            "target_id": <str|null>,   # null → text-only step in SDK
            "style":     <str>,
            "label":     <str>,
            "wait_for":  <str>,
        }
        """
        steps = self.parse_steps(llm_response_text)
        overlay_steps = []

        for idx, step_text in enumerate(steps, start=1):
            target_id = await self.resolve_widget(app_id, step_text)
            style = _assign_style(step_text)
            wait_for = _assign_wait_for(step_text)

            overlay_steps.append({
                "step": idx,
                "target_id": target_id,
                "style": style,
                "label": step_text,
                "wait_for": wait_for,
            })
            logger.debug(
                "Overlay step %d: target=%s style=%s label=%r",
                idx, target_id, style, step_text,
            )

        return overlay_steps
