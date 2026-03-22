"""
aggregator.py
-------------
Handles GROUP BY col with COUNT aggregation.

Returns a list of dicts: [{group_col: value, 'count': n}, ...]
sorted by count descending.
"""


def group_and_count(rows, group_col):
    """
    Group rows by group_col and count occurrences.

    Parameters
    ----------
    rows      : list of dicts
    group_col : str — column to group on

    Returns
    -------
    list of dicts sorted by count descending
    """
    if not rows:
        return []

    # Validate column exists
    if group_col not in rows[0]:
        raise KeyError(
            f"GROUP BY column '{group_col}' not found. "
            f"Available: {', '.join(rows[0].keys())}"
        )

    counts = {}
    for row in rows:
        key = row[group_col]
        counts[key] = counts.get(key, 0) + 1

    result = [
        {group_col: key, "count": count}
        for key, count in counts.items()
    ]

    return sorted(result, key=lambda r: r["count"], reverse=True)
