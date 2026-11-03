"""Independent finite witness model. No VATE imports or record-validation code.

History fields are illustrative integer seconds in one accepted clock domain.
Only the visible-attempt projection is observed; issuer counts are declarations,
not constraints on factual histories unless separately admitted as true.
"""
def evaluate(histories, visible_ids):
    projections = [[a for a in h if a['id'] in visible_ids] for h in histories]
    if not histories or any(p != projections[0] for p in projections):
        raise ValueError('a nonempty common observation fibre is required')
    def count(h):
        return sum(a['start'] < 1 < a['finish'] and a['commit'] is not None
                   and a['commit'] > 1 for a in h)
    totals = [count(h) for h in histories]
    return {'positive_in_every_history': all(n > 0 for n in totals),
            'zero_in_every_history': all(n == 0 for n in totals),
            'exact_count_established': len(set(totals)) == 1,
            'compatible_counts': sorted(set(totals)),
            'visible_positive_lower_bound': count(projections[0])}
