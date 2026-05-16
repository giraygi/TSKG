"""
Fetches Matomo CustomDimensions data and aggregates nb_actions per ontology.

Ontology names are extracted from label strings via two patterns:
  1. Path-based  : /ontologies/<name>[/...]   e.g. /api/v2/ontologies/efo/classes
  2. Param-based : ontology=<name>            e.g. ontology=ohdab
"""

import re
import json
import argparse
import requests
from collections import defaultdict

# ── Configuration ─────────────────────────────────────────────────────────────

MATOMO_URL  = "https://support.tib.eu/piwik/index.php"
TOKEN_AUTH  = "your1token2here3your4token5here6"        # <-- replace with your token
ID_SITE     = "35"
ID_DIM      = "4"
PERIOD      = "range"
DATE        = "last30"
FILTER_LIMIT= "-1"

# ── Patterns to detect ontology names ─────────────────────────────────────────

# /ontologies/<name>  (path segment after the keyword "ontologies")
RE_PATH  = re.compile(r'/ontologies/([A-Za-z0-9_\-]+)', re.IGNORECASE)

# ontology=<name>  (query-param style)
RE_PARAM = re.compile(r'\bontology=([A-Za-z0-9_\-]+)', re.IGNORECASE)


def fetch_data() -> list[dict]:
    """Call the Matomo API and return the parsed JSON list."""
    params = {
        "module":       "API",
        "method":       "CustomDimensions.getCustomDimension",
        "idDimension":  ID_DIM,
        "idSite":       ID_SITE,
        "period":       PERIOD,
        "date":         DATE,
        "format":       "json",
        "filter_limit": FILTER_LIMIT,
        "token_auth":   TOKEN_AUTH,
    }
    response = requests.post(MATOMO_URL, data=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    # Matomo sometimes wraps errors in a dict
    if isinstance(data, dict) and data.get("result") == "error":
        raise RuntimeError(f"Matomo API error: {data.get('message')}")

    return data


def extract_ontologies(label: str) -> list[str]:
    """
    Return a deduplicated list of ontology names found in *label*.

    Handles both:
      • /ontologies/efo/classes  →  ['efo']
      • ontology=ohdab           →  ['ohdab']
    """
    names = set()
    for m in RE_PATH.finditer(label):
        names.add(m.group(1).lower())
    for m in RE_PARAM.finditer(label):
        names.add(m.group(1).lower())
    return list(names)


def aggregate(records: list[dict]) -> dict[str, int]:
    """
    Walk every record, detect ontologies in its label, and accumulate nb_actions.
    Records with no detectable ontology are counted under '__no_ontology__'.
    """
    counts: dict[str, int] = defaultdict(int)

    for rec in records:
        label      = rec.get("label", "")
        nb_actions = int(rec.get("nb_actions", 0))
        ontologies = extract_ontologies(label)

        if ontologies:
            for onto in ontologies:
                counts[onto] += nb_actions
        else:
            counts["__no_ontology__"] += nb_actions

    return dict(counts)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Matomo data and aggregate nb_actions per ontology."
    )
    parser.add_argument(
        "--min-actions",
        type=int,
        default=0,
        metavar="N",
        help="Only show ontologies with nb_actions >= N (default: 0, i.e. show all).",
    )
    args = parser.parse_args()

    print("Fetching data from Matomo …")
    records = fetch_data()
    print(f"  → {len(records)} records received.\n")

    counts = aggregate(records)

    # Sort by nb_actions descending, then apply the lower-limit filter
    sorted_counts = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    filtered_counts = [(onto, n) for onto, n in sorted_counts if n >= args.min_actions]

    if args.min_actions:
        print(f"Showing ontologies with nb_actions >= {args.min_actions:,}  "
              f"({len(filtered_counts)} of {len(sorted_counts)} total)\n")

    print(f"{'Ontology':<30}  {'nb_actions':>12}")
    print("-" * 45)
    for onto, actions in filtered_counts:
        print(f"{onto:<30}  {actions:>12,}")

    # Optionally save to JSON
    output_path = "ontology_action_counts.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(dict(filtered_counts), fh, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
