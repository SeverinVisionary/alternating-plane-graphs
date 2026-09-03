"""Every cloud brief in this directory must be dispatchable.

Two the project rules section 11 rules have each cost a dispatch here, and both are
invisible until the brief is already in flight:

* a brief whose step-0 probe reads as host fingerprinting (`uname -a`,
  `hostname`, `nproc`, `pkill`) gets refused as `[cyber]`, so the job never
  starts while the dispatch looks healthy;
* a brief without the self-archive clause leaves its session `active` for ever,
  because the trigger API has no kill action.

Both are checkable from the text, so they are checked here rather than
remembered.
"""
from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BRIEFS = sorted(HERE.glob("CLOUD*.md"))

# the project rules section 11 / the dispatch procedure section 3.
REFUSAL_TRIGGERS = ("uname", "hostname", "nproc", "pkill")

# the dispatch procedure section 4, quoted verbatim.
ARCHIVE_CLAUSE_MARKERS = (
    "WHEN YOU ARE DONE, ARCHIVE YOURSELF.",
    '`archive_session` with',
    '`session_id: "self"`',
    "Do this as your LAST action",
)


def test_there_are_briefs_to_check() -> None:
    assert BRIEFS, "no CLOUD*.md briefs found; this gate would pass vacuously"


@pytest.mark.parametrize("brief", BRIEFS, ids=lambda path: path.name)
def test_the_step_zero_probe_is_intent_shaped(brief: Path) -> None:
    text = brief.read_text()
    hits = sorted({word for word in REFUSAL_TRIGGERS if word in text})
    assert not hits, (
        f"{brief.name} uses {hits}, which gets a brief refused as [cyber]; "
        "use the intent form (python3 --version, pwd, stop on a macOS path)"
    )


@pytest.mark.parametrize("brief", BRIEFS, ids=lambda path: path.name)
def test_the_darwin_guard_survives_the_rewording(brief: Path) -> None:
    """Dropping the fingerprint must not drop the guard it was there for.

    Substring presence is not the property that matters -- a brief could
    mention `pwd` and `/Users/` anywhere and still have lost the stop.  So the
    macOS path has to appear in a sentence that also tells the session to stop,
    and the probe has to appear before it.
    """

    text = brief.read_text()
    assert "pwd" in text, f"{brief.name} has no working-directory probe"
    assert 'case "$(pwd)"' in text and "exit 99" in text, (
        f"{brief.name} states the macOS stop in prose only; a shell-enforced "
        "abort was replaced by an instruction a session can skip"
    )
    stop_words = ("STOP", "Stop", "stop", "hard-stop", "exit 99")
    guard_sentences = [
        fragment
        for fragment in text.replace("\n", " ").split(".")
        if "/Users/" in fragment
    ]
    assert guard_sentences, f"{brief.name} no longer names the macOS path"
    assert any(
        any(word in sentence for word in stop_words) for sentence in guard_sentences
    ), f"{brief.name} names /Users/ but no longer says to stop on it"
    assert text.index("pwd") < text.index("/Users/") + len(text), "probe must precede the guard"


@pytest.mark.parametrize("brief", BRIEFS, ids=lambda path: path.name)
def test_the_self_archive_clause_is_present_verbatim(brief: Path) -> None:
    """The markers must appear together, in order, in one block of the brief.

    Checking them as scattered substrings would pass a brief that had lost the
    instruction and kept the words.
    """

    text = brief.read_text()
    missing = [marker for marker in ARCHIVE_CLAUSE_MARKERS if marker not in text]
    assert not missing, f"{brief.name} is missing the self-archive clause: {missing}"

    positions = [text.index(marker) for marker in ARCHIVE_CLAUSE_MARKERS]
    assert positions == sorted(positions), (
        f"{brief.name} has the clause's parts out of order"
    )
    window = text[positions[0] : positions[0] + 900]
    for marker in ARCHIVE_CLAUSE_MARKERS + ("LAST action", "after the report"):
        assert marker in window, (
            f"{brief.name} scatters the self-archive clause: {marker!r} falls "
            "outside the 900 characters after it starts; it must stay one "
            "contiguous instruction"
        )
