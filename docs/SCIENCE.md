# Scientific Grounding

This system models post-harvest banana (Cavendish, *Musa acuminata* AAA) shelf life using a physics-based simulator calibrated to published respiration and storage parameters. The same equations drive both the synthetic training data and the live forward-projection that produces "Days until spoilage" labels.

## 1. Reference parameters

| Parameter | Value | Source |
|---|---|---|
| Optimal storage temperature | 13–14 °C | UC Davis Postharvest Technology Center |
| Optimal relative humidity | 90–95 % | UC Davis Postharvest Technology Center |
| Shelf life @ 14 °C in air | 14–28 days | UC Davis Postharvest Technology Center |
| Shelf life @ 27 °C (room) | 7 d untreated / 11 d w/ 1-MCP | Academia.edu — banana 1-MCP shelf-life study |
| Climacteric peak respiration (untreated) | 56.8 mg CO₂ / kg / h | ResearchGate — Goldfinger banana respiration study |
| Climacteric peak with ethylene exposure | up to 74.2 mg CO₂ / kg / h | ResearchGate — Goldfinger banana respiration study |
| Ripe banana CO₂ rate | ~7.6 L CO₂ / kg / h | ResearchGate — banana aerobic respiration |
| Cold (pre-climacteric) CO₂ rate | ~1.2 L CO₂ / kg / h | ResearchGate — banana aerobic respiration |
| Ethylene production peak | up to 7.4 µL C₂H₄ / kg / h | ResearchGate — banana aerobic respiration |
| Chilling injury threshold | < 13 °C | UC Davis |
| CO₂ toxicity threshold | > 7 % (70,000 ppm) | UC Davis |

The full numeric set lives in `data/references/banana_postharvest_constants.json` and is exposed read-only by the API at `GET /api/reference/banana`.

## 2. Modeling laws

**Arrhenius temperature dependence**

```
k(T) = A · exp( -Ea / (R · T) )
```

We use it as a *factor* relative to a reference temperature `T_ref = 14 °C`:

```
factor(T) = exp( -Ea/R · (1/T_K  -  1/T_ref_K) )
```

with `Ea = 80,000 J/mol` (a representative value for fruit respiration) and `R = 8.314 J/mol·K`. Empirically this gives roughly `Q10 ≈ 2.5` over the 0–40 °C range, matching published banana behaviour.

**Climacteric multiplier.** The respiration rate is not monotonic with ripeness: it climbs through the climacteric peak, drops post-peak, and rises again at senescence. We implement this as a piecewise function calibrated so the peak (10 mg/kg/h base × ~5.5 multiplier ≈ 55 mg/kg/h) matches the published 56.8 figure.

**Humidity stress.** Deviation from 92.5 % RH adds linearly to a "stress" multiplier on the biological aging clock (`1 + 0.02·|RH − 92.5|`). Low humidity drives moisture loss; very high humidity invites fungal growth.

**Container gas balance.** The storage container is modelled as a fixed-volume box with a leak rate `k_leak`:

```
dC/dt  =  ( production_rate · mass_kg / V )  −  k_leak · C
```

This produces realistic rise-and-plateau curves rather than unbounded ramps, and lets us simulate poorly ventilated bags by lowering `k_leak`.

**Anaerobic spoilage.** Methane is a byproduct of late-stage anaerobic decomposition, not normal banana respiration. We turn methane production on only after ripeness stage 7.2 — once methane is detectable, spoilage is irreversible.

## 3. Spoilage definition

A batch is considered spoiled when *any* of:
1. ripeness stage ≥ 7 (peel browning, flesh softening past edibility);
2. cumulative environmental stress integral exceeds threshold (representing the integrated effect of out-of-range conditions over time);
3. methane appears in the headspace (anaerobic decomposition started).

`days_until_spoilage` is computed by projecting forward from the current state with conditions held constant — so the label answers *"if conditions stay like this, how many days remain?"*.

## 4. Validation strategy

This MVP is trained on physics-simulated data, not real sensor logs. Reported metrics in `ml/artifacts/metadata.json` therefore measure two things:

1. **Algorithmic ability to learn the simulator's underlying physics** — held-out batches at unseen condition combinations.
2. **Qualitative agreement with published shelf-life tables** — predicted RSL at 14 °C / 92 % RH should fall in the 14–28 day window; at 22 °C / 65 % RH should fall in the 7–11 day window.

Real-sensor validation is explicit future work (see Roadmap in `README.md`).

## 5. Citations

- UC Davis Postharvest Technology Center — *Banana Recommendations for Maintaining Postharvest Quality*. https://postharvest.ucdavis.edu/Commodity_Resources/Fact_Sheets/Datastores/Fruit_English/?uid=11&ds=798
- Chitarra, M.I. & Chitarra, A.B. *Pós-Colheita de Frutas e Hortaliças* (banana ripeness scale).
- Goldfinger banana respiration study (ResearchGate).
- Banana shelf-life study with 1-MCP at 27 °C (Academia.edu).
