"""Reciprocal rank fusion, which merges ranked lists without comparing scores.

Each featurizer scores similarity on its own scale, so the scores cannot be
pooled. Only the ranks are comparable, and that is all this uses.
"""


def fuse(rankings, k, top):
    """Merge ranked lists of hit ids into a single ranked list.

    A hit scores ``1 / (k + rank)`` in every list that holds it, and the scores
    are summed. `k` sets how far a hit's position counts against how many lists
    found it: a hit that two lists rank at ``k + 1`` or better beats a hit that
    one list ranks first.

    Parameters
    ----------
    rankings : list of list of str
        One ranked list of hit ids per featurizer, most similar first.
    k : int
        Rank damper. 0 makes the first rank dominate, large values count lists.
    top : int
        How many hits to return.

    Returns
    -------
    list of str
        At most `top` hit ids, best first. Ties break by hit id, so the same
        query always gives the same answer.
    """
    scores = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, 1):
            scores[hit] = scores.get(hit, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda hit: (-scores[hit], hit))[:top]
