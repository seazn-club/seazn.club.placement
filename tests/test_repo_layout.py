"""This repo is the placement service at its root; the docs and comments were
written for the service's old home inside seazn.club. These pins keep the
move honest.

Every sweep reports what it scanned and zero scanned is a FAILURE
(seazn.club's TEST-STRATEGY.md, see AGENTS.md, "Paths in comments": anti-vacuity).
The old-layout needles are assembled from pieces so this file does not match its
own sweep.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

OLD_LAYOUT_NEEDLES = ("services/" "placement", "../" "../")
SWEPT_SUFFIXES = {".md", ".py", ".toml", ".yml"}
SWEPT_NAMES = {"Dockerfile"}
# The ONE place the old path is meant to appear: AGENTS.md's history pointer,
# a git command that runs in a seazn.club checkout. Matched as an exact line.
ALLOWED_LINES = {
    ("AGENTS.md", "`git log placement-split-base -- services/" "placement proto` (tag at"),
}
# Files the sweep must have read, or it swept the wrong tree.
ANCHORS = {
    "README.md", "AGENTS.md", "DEPLOY.md", "Dockerfile", "fly.toml", "pyproject.toml",
    ".github/workflows/ci.yml", "tests/test_proto_compiles.py", "src/placement/main.py",
    "bench/README.md",
}


# The GitHub owner this repository, its image and its sibling repositories had before
# they moved to the seazn-club org. Assembled from pieces so this file does not match
# its own sweep. Two repositories stayed with the old owner: naming those is current.
OLD_OWNER = "on" "ryde"
STAYED_WITH_OLD_OWNER = tuple(f"{OLD_OWNER}/seazn.club.{name}" for name in ("workflow", "outbox"))
# The ONE line that may still name the old owner: DEPLOY.md's history of the package
# this repository published to before the move. Matched as an exact line.
OWNER_ALLOWED_LINES = {
    ("DEPLOY.md", f"**History.** The package was first `ghcr.io/{OLD_OWNER}/seazn-placement`. It was deleted and"),
}
# Files the old-owner sweep must have read: everything that names the image, the
# label or the repository URL.
OWNER_ANCHORS = {
    "README.md", "AGENTS.md", "DEPLOY.md", "Dockerfile", "bench/README.md",
    ".github/workflows/ci.yml", ".github/workflows/stg.yml", ".github/workflows/prod.yml",
    "scripts/publish-image.sh", "scripts/require-image.sh",
    "tests/test_publish_image.py", "tests/test_deploy_scripts.py",
}


def _repo_files():
    """Tracked files plus untracked-but-not-ignored ones, so the sweep also sees
    work that is not committed yet. Raises (a failure) outside a git checkout."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=REPO_ROOT, capture_output=True, check=True,
    )
    return sorted(n for n in result.stdout.decode().split("\0") if n)


def _swept(rel):
    path = Path(rel)
    return path.suffix in SWEPT_SUFFIXES or path.name in SWEPT_NAMES


def test_no_old_layout_paths_in_tracked_text():
    scanned = []
    allowed_hits = {}
    for rel in _repo_files():
        if not _swept(rel):
            continue
        scanned.append(rel)
        for number, line in enumerate((REPO_ROOT / rel).read_text().splitlines(), 1):
            if not any(needle in line for needle in OLD_LAYOUT_NEEDLES):
                continue
            key = (rel, line.strip())
            if key in ALLOWED_LINES:
                allowed_hits[key] = allowed_hits.get(key, 0) + 1
                continue
            raise AssertionError(f"{rel}:{number}: old-layout path: {line.strip()}")
    assert len(scanned) > 0, "no file was scanned; the sweep is vacuous"
    missing = ANCHORS - set(scanned)
    assert not missing, f"the sweep did not read {sorted(missing)} (scanned {len(scanned)} files)"
    # An allowlist entry that matches nothing is stale and would hide a real hit later.
    assert allowed_hits == {key: 1 for key in ALLOWED_LINES}, allowed_hits


def _names_the_old_owner(line):
    rest = line.lower()
    for repo in STAYED_WITH_OLD_OWNER:
        rest = rest.replace(repo, "")
    return OLD_OWNER in rest


def test_the_old_owner_predicate_spares_only_the_repositories_that_stayed():
    # Both directions: a predicate that flags nothing would make the sweep below vacuous,
    # and one that flags the staying repositories would force them into the allowlist.
    cases = {
        f"ghcr.io/{OLD_OWNER}/seazn-placement:abc": True,
        f"https://github.com/{OLD_OWNER}/seazn.club.placement": True,
        f"gh api orgs/{OLD_OWNER}/packages/container/seazn-placement": True,
        f"{OLD_OWNER.capitalize()}/seazn.club.engine": True,
        f"{OLD_OWNER}/seazn.club.workflow and {OLD_OWNER}/seazn.club.engine": True,
        f"{OLD_OWNER}/seazn.club.workflow": False,
        f"https://github.com/{OLD_OWNER}/seazn.club.outbox": False,
        "ghcr.io/seazn-club/seazn-placement:abc": False,
    }
    assert {line: _names_the_old_owner(line) for line in cases} == cases


def test_nothing_points_at_the_old_github_owner():
    # The repository and its image moved to the seazn-club org, and GitHub cannot move a
    # package between owners. A leftover old-owner name is a push to, or a deploy from, a
    # package that is no longer this repository's, or a link to a moved repository.
    # Every tracked text file, not a suffix list: a .sh script holds the image name.
    scanned = []
    allowed_hits = {}
    for rel in _repo_files():
        try:
            text = (REPO_ROOT / rel).read_text()
        except UnicodeDecodeError:
            continue
        scanned.append(rel)
        for number, line in enumerate(text.splitlines(), 1):
            if not _names_the_old_owner(line):
                continue
            key = (rel, line.strip())
            if key in OWNER_ALLOWED_LINES:
                allowed_hits[key] = allowed_hits.get(key, 0) + 1
                continue
            raise AssertionError(f"{rel}:{number}: names the old GitHub owner: {line.strip()}")
    assert len(scanned) > 0, "no file was scanned; the sweep is vacuous"
    missing = OWNER_ANCHORS - set(scanned)
    assert not missing, f"the sweep did not read {sorted(missing)} (scanned {len(scanned)} files)"
    # An allowlist entry that matches nothing is stale and would hide a real hit later.
    assert allowed_hits == {key: 1 for key in OWNER_ALLOWED_LINES}, allowed_hits


def test_gitignore_keeps_env_files_out_of_the_repo():
    # The repo is public. A local .env must never be committable by accident.
    names = [".env", ".env.local", ".env.production", ".env.test.local"]
    result = subprocess.run(
        ["git", "check-ignore", "--verbose", "--no-index", *names],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    ignored = {line.split("\t", 1)[1] for line in result.stdout.splitlines()}
    assert ignored == set(names), (result.stdout, result.stderr)
