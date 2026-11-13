"""The result tables the commands print: the summary and the upset views, as plain text.

Each row shows the counts next to the rate, with a bar to make the pattern easy to see.
Plain ASCII only, so it prints the same in any terminal.
"""

BAR_WIDTH = 20


def bar(rate_pct, width=BAR_WIDTH):
    filled = round(rate_pct / 100 * width)
    return "#" * filled + "." * (width - filled)


def _row(label, games, won, rate, label_width):
    return f"  {label!s:<{label_width}.{label_width}} {games:>7} {won:>7} {rate:>6.1f}%  {bar(rate)}"


def format_summary(rows):
    """Higher-rated win rate by rating-gap band, then the overall rate worked out from counts."""
    if not rows:
        return "Higher-rated win rate, by rating gap\n  no games to count"
    lines = [
        "Higher-rated win rate, by rating gap",
        f"  {'gap band':<10} {'games':>7} {'won':>7} {'rate':>7}",
    ]
    lines += [_row(*row, label_width=10) for row in rows]
    games = sum(row[1] for row in rows)
    won = sum(row[2] for row in rows)
    rate = 100.0 * won / games
    lines.append(
        f"overall: {games} games, {won} won by the higher-rated player ({rate:.1f}%)"
    )
    return "\n".join(lines)


def _table(title, label_name, rows, limit=None):
    lines = [title, f"  {label_name:<28} {'games':>7} {'upsets':>7} {'rate':>7}"]
    shown = rows if limit is None else rows[:limit]
    lines += [_row(*row, label_width=28) for row in shown]
    if not rows:
        lines.append("  no games to count")
    if limit is not None and len(rows) > limit:
        lines.append(f"  ... {len(rows) - limit} more openings not shown")
    return "\n".join(lines)


def format_upsets(upsets, top_openings=10):
    """How often the lower-rated player wins, by opening, by how the game ended and by length."""
    sections = [
        "Upsets: how often the lower-rated player wins",
        _table(
            f"By opening (the {top_openings} most played)",
            "opening",
            upsets["opening"],
            top_openings,
        ),
        _table("By how the game ended", "ending", upsets["ending"]),
        _table("By game length (moves by both players)", "length", upsets["length"]),
    ]
    return "\n\n".join(sections)
