"""Portable structural validation for the committed Halo skill package."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "skills" / "halo-research"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\n") or "\nname: halo-research\n" not in skill:
        raise SystemExit("invalid halo-research skill frontmatter")
    if "\ndescription:" not in skill.split("---", 2)[1]:
        raise SystemExit("skill description is missing")
    references = {
        "HALO-RESEARCH-GATEWAY-SPEC.md",
        "source-selection.md",
        "citation-contract.md",
        "limitations.md",
        "host-tool-mapping.md",
    }
    missing = [name for name in references if not (root / "references" / name).is_file()]
    if missing:
        raise SystemExit(f"missing skill references: {missing}")
    spec = root / "references" / "HALO-RESEARCH-GATEWAY-SPEC.md"
    governing = root.parents[1] / "docs" / "HALO-RESEARCH-GATEWAY-SPEC-v1.5.md"
    if spec.read_bytes() != governing.read_bytes():
        raise SystemExit("skill-bundled specification differs from governing v1.5 document")
    if "TODO" in skill or "[TODO" in skill:
        raise SystemExit("unfinished skill placeholder")
    print("halo-research skill package valid")


if __name__ == "__main__":
    main()
