"""Search the Enamine Hit Locator Library with three featurizers and fuse the hits.

lazy-sim searches one index at a time, so each featurizer is searched for its own
top `TOP` and the three rankings are then merged by reciprocal rank fusion.
"""

import csv
import os
import tempfile

from fuse import fuse

FEATURIZERS = ("clamp", "sand", "moljepa")
TOP = 100
RRF_K = 10

_ROOT = os.path.dirname(os.path.abspath(__file__))
CHECKPOINTS = os.path.abspath(os.path.join(_ROOT, "..", "..", "checkpoints"))
LIBRARY = os.path.join(CHECKPOINTS, "library")

# lazy-sim downloads a featurizer's weights unless these point at a local copy.
# They are bundled in model/checkpoints, which is fetched at runtime from eosvc.
_WEIGHTS = {
    "LAZYSIM_CLAMP_WEIGHTS": "clamp_compound_encoder_v1.npz",
    "LAZYSIM_SAND_WEIGHTS": "sand_encoder_v1.npz",
    "LAZYSIM_MOLJEPA_WEIGHTS": "moljepa_4c912b4.safetensors",
}
for _var, _file in _WEIGHTS.items():
    os.environ.setdefault(_var, os.path.join(CHECKPOINTS, "weights", _file))


def _write_queries(smiles_list, path):
    """Name each query after its row, so hits map back even for repeated SMILES."""
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "smiles"])
        writer.writerows([f"q{i}", smiles] for i, smiles in enumerate(smiles_list))


def _read_hits(path, smiles_of):
    """Return ``{query_id: [hit_id by rank]}`` and record each hit's SMILES."""
    ranked = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            ranked.setdefault(row["query_id"], []).append(
                (int(row["rank"]), row["hit_id"])
            )
            smiles_of[row["hit_id"]] = row["hit_smiles"]
    return {q: [hit for _, hit in sorted(hits)] for q, hits in ranked.items()}


def neighbours(smiles_list):
    """Return each query's `TOP` nearest library molecules, fused over FEATURIZERS.

    Parameters
    ----------
    smiles_list : list of str
        Query molecules.

    Returns
    -------
    list of list of str
        One row per query, holding `TOP` library SMILES, most similar first.
        A query no featurizer could parse gives a row of empty strings.
    """
    import lazy_sim

    smiles_of = {}
    per_featurizer = []
    with tempfile.TemporaryDirectory() as tmp:
        queries = os.path.join(tmp, "queries.csv")
        _write_queries(smiles_list, queries)
        for featurizer in FEATURIZERS:
            hits = os.path.join(tmp, f"{featurizer}.csv")
            lazy_sim.search(queries, LIBRARY, hits, featurizer, k=TOP)
            per_featurizer.append(_read_hits(hits, smiles_of))

    rows = []
    for i in range(len(smiles_list)):
        query = f"q{i}"
        rankings = [r[query] for r in per_featurizer if query in r]
        fused = fuse(rankings, k=RRF_K, top=TOP) if rankings else []
        row = [smiles_of[hit] for hit in fused]
        rows.append(row + [""] * (TOP - len(row)))
    return rows
