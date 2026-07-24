# 1E-V-CLASSIFY — Vedic Admission Classification

**Status:** complete · **Type:** architectural decomposition, not a dictionary
· **Produces:** no denotations · **Part of:**
[Representation 1E](REPRESENTATION_1E_CROSS_SYSTEM_DENOTATION.md)

The deliverable is a decomposition, grounded in what the Vedic code actually
computes. As with gematria, it is also a test of whether the 1E governance
architecture is system-independent — and Vedic decomposes into **more layers
than either prior system**, with two school-specific choices that neither
numerology nor gematria has any analogue for.

```text
numerology   2 layers
gematria     6 layers
vedic        8 layers
```

---

## What the code computes

- `temporal/ephemeris.py` — tropical geocentric positions (Swiss Ephemeris)
- `temporal/sidereal.py`, `temporal/dasha.py` — ayanamsa: Lahiri (default),
  Raman, Krishnamurti
- `temporal/houses.py` — Whole Sign only (`raises` on any other system)
- `temporal/nakshatra.py` — 27-fold division of the ecliptic
- `temporal/vargas.py`, `navamsa.py` — divisional charts
- `temporal/vimshottari_dasha.py` — dasha periods (Ketu 7 … 120-year total)
- `knowledge/dignities.py`, `yogas.py` — exaltation, debilitation, yoga rules
- `knowledge/planets.py`, `vedic_interpreter.py`,
  `interpretation/vedic_behavior.py` — interpretive text, **uncited**

---

## The load-bearing finding: ayanamsa

Vedic is **sidereal**, so tropical ephemeris positions must be offset by an
ayanamsa before any sign, nakshatra, or house is assigned. The code supports
three — Lahiri, Raman, Krishnamurti — and they **disagree**, by arcminutes to
more than a degree, which shifts nakshatra boundaries and occasionally sign
boundaries.

The offset *value* is computed by Swiss Ephemeris (like Unicode sourcing Hebrew
identity), but **which ayanamsa** is a school-specific claim requiring a
source. It is the choice on which every downstream sidereal quantity depends,
and it has no numerology or gematria analogue: numerology had a reduction
policy, gematria a transliteration and a value method, but neither had a
contested global coordinate frame under everything.

A second such choice sits alongside it: **house system**. `build_house_chart`
implements Whole Sign only and raises on others, so a school default is baked
in without being declared as one tradition among several.

---

## Layer decomposition and admission

| layer | class | admitted | why |
|---|---|---|---|
| ephemeris | derived computation | **yes** | Swiss Ephemeris, pinned, reproducible |
| ayanamsa_framework | textual interpretation | no | school choice, undeclared as sourced |
| house_system | textual interpretation | no | Whole Sign baked in, unsourced |
| nakshatra_assignment | derived computation | yes* | deterministic on sidereal longitude |
| divisional_charts | derived computation | yes* | deterministic transforms |
| dasha_system | hybrid | no | period values traditional and uncited |
| dignity_and_yoga_rules | textual interpretation | no | rules hardcoded, uncited |
| denotation | textual interpretation | no | interpretive text, no provenance |

\* Admitted **in isolation only**. Nakshatra assignment and vargas are
deterministic, but they consume ayanamsa-offset longitudes — and a layer's
admission covers its own operation, never its inputs. While the ayanamsa is
unlicensed they contribute nothing, exactly as gematria's numeric computation
does over unlicensed transliteration.

`admissible_in_isolation("vedic")` = `[ephemeris, nakshatra_assignment,
divisional_charts]`. Three admitted layers, and **Vedic denotes nothing.**

---

## Dasha is hybrid

Vimshottari period lengths — Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7,
Rahu 18, Jupiter 16, Saturn 19, Mercury 17, summing to 120 years — are
traditional **values** hardcoded with no citation, while the period arithmetic
is deterministic. So the layer is hybrid: reproducible computation over an
uncited traditional table, and Vimshottari is itself one dasha system among
several. Not admitted.

---

## Denotation is uncited, and quarantined

`knowledge/planets.py` carries text like *"the Sun represents conscious
identity, vitality, purpose…"* with no source of any kind — verified: no
citation, source id, or locator anywhere in the interpretation modules. This
is the Vedic equivalent of `evidence_from_number` and the numerology synthesis
layers: the largest accidental-entry path.

It is added to `INTERPRETATION_QUARANTINE`, now one entry per system
(numerology, gematria, vedic), and an AST test asserts no module under
`validation/denotation/` imports any of them.

---

## Result

Vedic is **not admitted at any denoting layer**. Three computational layers are
admitted in isolation and none can feed a denotation, because the ayanamsa
framework beneath them all is an unlicensed school choice.

The methodology test holds a third time: applying the 1E process to Vedic
produced a genuinely different decomposition — eight layers, a contested global
coordinate frame, a hybrid dasha layer — none of it inherited from numerology
or gematria by analogy.

`concordance_ready` stays **false**. Only Kamea denotes.

### The path to admission

1. **1E-V-SOURCE-A** — declare and source the ayanamsa framework and house
   system (school-specific choices), so sidereal quantities become licensed.
2. **1E-V-SOURCE-B** — source the dasha period table and dignity/yoga rules.
3. **1E-V-SOURCE-C** — historically licensed denotation, behind a citation
   corpus.

As with gematria, some of this is source-neutral (declaring the ayanamsa as a
*choice* with a recorded value) and some needs real sources (the traditional
tables and interpretations).
