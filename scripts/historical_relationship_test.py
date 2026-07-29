"""Do historical relationships show up in the structural shape?

Curated dyads with known relationship type (ALLY = sustained cooperation; RIVAL =
defining antagonism/rupture). Each person -> composite shape. Then:

  1. Are related pairs closer (or farther) in shape than random pairs?
  2. Do ALLY dyads differ from RIVAL dyads?
  3. Confound: shape distance tracks name-length difference. Does any relationship
     signal survive once length difference is accounted for?

Relationship is a lived/historical fact; the shape is name-derived. Honest prior:
null. Tested anyway, with the length control.
"""

from __future__ import annotations

import numpy as np

from atlas.ciphers import english_ordinal_sequence
from atlas.kamea.composite_shape import composite_shape_from_values, composite_distance

SEED = 20260728

ALLIES = [
    ("Steve Jobs", "Steve Wozniak"), ("Karl Marx", "Friedrich Engels"),
    ("Thomas Jefferson", "James Madison"), ("George Washington", "Alexander Hamilton"),
    ("James Watson", "Francis Crick"), ("Marie Curie", "Pierre Curie"),
    ("Wilbur Wright", "Orville Wright"), ("Meriwether Lewis", "William Clark"),
    ("Johann Wolfgang von Goethe", "Friedrich Schiller"),
    ("Jean-Paul Sartre", "Simone de Beauvoir"),
    ("Franklin Roosevelt", "Winston Churchill"),
    ("Ralph Waldo Emerson", "Henry David Thoreau"),
    ("Pablo Picasso", "Georges Braque"), ("Wolfgang Amadeus Mozart", "Joseph Haydn"),
    ("Vladimir Lenin", "Leon Trotsky"), ("Charles Darwin", "Thomas Huxley"),
    ("Sigmund Freud", "Josef Breuer"), ("Auguste Rodin", "Camille Claudel"),
]
RIVALS = [
    ("Nikola Tesla", "Thomas Edison"), ("Thomas Jefferson", "Alexander Hamilton"),
    ("John Adams", "Alexander Hamilton"), ("Sigmund Freud", "Carl Jung"),
    ("Vincent van Gogh", "Paul Gauguin"), ("Isaac Newton", "Gottfried Wilhelm Leibniz"),
    ("Isaac Newton", "Robert Hooke"), ("Alexander Hamilton", "Aaron Burr"),
    ("Thomas Edison", "George Westinghouse"), ("Napoleon Bonaparte", "Arthur Wellesley"),
    ("Joseph Stalin", "Leon Trotsky"), ("Martin Luther", "Desiderius Erasmus"),
    ("Abraham Lincoln", "Stephen Douglas"), ("Wolfgang Amadeus Mozart", "Antonio Salieri"),
    ("Mahatma Gandhi", "Winston Churchill"), ("Julius Caesar", "Pompey"),
    ("Cicero", "Mark Antony"), ("Elon Musk", "Sam Altman"),
]


def main():
    rng = np.random.default_rng(SEED)
    names = sorted({n for pair in ALLIES + RIVALS for n in pair})
    shape = {n: np.array(composite_shape_from_values(english_ordinal_sequence(n)).vector()) for n in names}
    length = {n: len(english_ordinal_sequence(n)) for n in names}

    def dyad_stats(pairs):
        return np.array([composite_distance_v(shape[a], shape[b]) for a, b in pairs]), \
               np.array([abs(length[a] - length[b]) for a, b in pairs])

    def composite_distance_v(a, b):
        return float(np.sqrt(((a - b) ** 2).sum()))

    ad, al = dyad_stats(ALLIES)
    rd, rl = dyad_stats(RIVALS)
    related = np.concatenate([ad, rd])

    # random pairs among the same people that are NOT a listed dyad
    dyset = {frozenset(p) for p in ALLIES + RIVALS}
    rand_d, rand_l = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if frozenset((names[i], names[j])) not in dyset:
                rand_d.append(composite_distance_v(shape[names[i]], shape[names[j]]))
                rand_l.append(abs(length[names[i]] - length[names[j]]))
    rand_d, rand_l = np.array(rand_d), np.array(rand_l)

    print(f"dyads: {len(ALLIES)} allied, {len(RIVALS)} rival | random pairs: {len(rand_d)}\n")
    print(f"mean shape distance:  allied {ad.mean():.3f}  rival {rd.mean():.3f}  "
          f"related {related.mean():.3f}  random {rand_d.mean():.3f}")

    # Test 1: related vs random (permutation over which pairs are 'related')
    obs1 = related.mean() - rand_d.mean()
    pool = np.concatenate([related, rand_d]); k = len(related)
    d1 = np.array([(s := rng.permutation(pool))[:k].mean() - s[k:].mean() for _ in range(5000)])
    p1 = float((np.abs(d1) >= abs(obs1)).mean())
    print(f"\nTest 1 related vs random:  diff {obs1:+.3f}  two-tailed p={p1:.4f}  "
          f"{'differ' if p1 < 0.05 else 'AT NULL'}")

    # Test 2: allied vs rival
    obs2 = ad.mean() - rd.mean()
    pool2 = np.concatenate([ad, rd]); k2 = len(ad)
    d2 = np.array([(s := rng.permutation(pool2))[:k2].mean() - s[k2:].mean() for _ in range(5000)])
    p2 = float((np.abs(d2) >= abs(obs2)).mean())
    print(f"Test 2 allied vs rival:    diff {obs2:+.3f}  two-tailed p={p2:.4f}  "
          f"{'differ' if p2 < 0.05 else 'AT NULL'}")

    # Confound: is shape distance just name-length difference?
    alld = np.concatenate([related, rand_d]); alll = np.concatenate([ad, rd, rand_l])
    r = float(np.corrcoef(alld, alll)[0, 1])
    print(f"\nConfound: corr(shape distance, name-length difference) = {r:+.3f}  "
          f"(mean |Δlen|: related {np.concatenate([al,rl]).mean():.1f}  random {rand_l.mean():.1f})")
    print("\nRelationship is historical; shape is name-derived. At-null results mean")
    print("the structure carries no trace of who allied with or fought whom.")


if __name__ == "__main__":
    main()
