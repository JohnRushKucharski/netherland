# Timestep Computation Reference

This document traces the full order of operations performed by `Cell.step_forward()` for a
single timestep. It covers every gain, loss, and internal transfer for each layer in the cell,
and describes how the surface elevation is updated at the end.

For the Morris & Bowden (1986) paper that motivates the model, see `Morris-SSAJ-1986.pdf` in
this directory.

---

## Inputs

At the start of each timestep the following are provided externally (typically by a coupled
sediment transport and vegetation model):

| Symbol | Argument | Unit | Description |
|--------|----------|------|-------------|
| `dep`  | `dep`    | cm   | Net deposition (+) or erosion (−) at the cell surface |
| R₀     | `top`    | g/cm² | Below-ground biomass concentration at the sediment surface |
| Δt     | `yrs`    | yr   | Length of the timestep |
| —      | `sub_steps` | — | Number of equal sub-steps (default 1; used to approximate continuous time) |

---

## Constants Used

The following constants from `constants.toml` govern this computation:

| Constant | Description |
|----------|-------------|
| k        | Specific decay rate of labile organic material [1/yr] |
| k1       | Biomass distribution decay parameter [1/cm] |
| k2       | Below-ground biomass turnover rate [1/yr] |
| k3       | Inorganic (ash) fraction of plant matter [g/g] |
| fc       | Refractory fraction of organic material [—] |
| fl = 1−fc | Labile fraction of organic material [—] |
| fo       | Organic fraction of deposited sediment [—] |
| fi = 1−fo | Inorganic fraction of deposited sediment [—] |
| rd       | Maximum root depth [cm] |
| wa\_to\_rl | Ratio of above- to below-ground biomass production (Wa/Rl) [—] |
| b        | Litter transport factor (b=0: all washes away; b=1: balanced; b>1: net import) [—] |
| bo, bi   | Bulk density of organic / inorganic matter [g/cm³] |
| sa       | Cell surface area [cm²] |

---

## Coordinate System

Depths are always measured **downward from the current surface**:

- Depth `0` = current ground surface (top of the topmost layer).
- Positive depth = below the surface.
- `layer.depths = (top, bottom)` where `top < bottom` and `bottom` is **fixed** for the
  lifetime of that layer.
- `cell.elevation` is the absolute elevation of the surface (e.g., cm above mean low water).

At the end of every timestep, the top of the topmost layer is always `0`.
All existing layers shift downward as new material is added.

---

## Computation Order

The computation proceeds in three stages:

1. **Pre-computation** — measure the cell state before anything changes.
2. **Existing layers** — update every existing layer from top to bottom.
3. **New top layer** — create and populate the layer representing this timestep's deposit.

---

### Stage 1 — Pre-computation (before any layer is touched)

```
total_biomass = Σ layer.stocks[0].weight   for all layers   [g]
```

This snapshot of total below-ground biomass is used for litter and cannot change once
computation begins.

If `sub_steps > 1`, the timestep is divided into `sub_steps` equal sub-intervals each of
duration `Δt / sub_steps`. Stage 1 is re-evaluated at the start of each sub-step using the
layers as they exist at that moment. Stage 3 (new top layer creation) occurs only on the
**first** sub-step.

---

### Stage 2 — Existing layers (top → bottom, `Layer.step_forward`)

Each existing layer is processed in order from **shallowest to deepest**.
Within each layer the following sub-steps run in sequence:

#### 2a. Biomass transfers

Biomass concentration at the top of this layer is read from the cell-wide exponential
distribution:

```
B(z) = R₀ × e^(−k1 × z) × sa      [g at depth z cm]
```

Then one of two tracks is taken depending on the sign of `dep`:

**Deposition track (`dep ≥ 0`):**

| Transfer | Formula | From → To |
|----------|---------|-----------|
| Turnover — labile fraction | B × k2 × fl × Δt | biomass → labile sediment (this layer) |
| Turnover — refractory fraction | B × k2 × fc × Δt | biomass → refractory sediment (this layer) |
| Turnover — inorganic fraction | 0 | (by assumption, M&B: root uptake = root death) |
| Burial (if layer crosses rd boundary) | mass of roots pushed below rd | biomass → labile/refractory/inorganic sediment (this layer) |

Turnover is treated as a **net gain**: new root growth instantaneously replaces dead roots
(M&B assumption preceding Eq. 10), so turnover output is added to sediment without reducing
the biomass stock.

**Erosion track (`dep < 0`):**

| Transfer | Formula | From → To |
|----------|---------|-----------|
| Turnover (same as above) | B × k2 × fl × Δt, etc. | biomass → sediment |
| Erosion of biomass | roots in eroded depth × (1−k3) × fl, etc. | biomass → **lost from system** |

#### 2b. Sediment losses (applied to all existing layers)

| Loss | Formula | Destination |
|------|---------|-------------|
| Labile decomposition | labile\_weight × k × Δt | leaves layer as CO₂, CH₄, dissolved nutrients (lost from system) |
| Inorganic ash uptake | biomass\_weight × k3 × wa\_to\_rl × Δt | leaves layer to support above-ground plant production (lost from system) |

> **Labile material** is organic sediment easily broken down by bacteria and microbes —
> simple sugars, proteins, amino acids, and lipids from fresh plant material, algae, and
> phytoplankton. When it decomposes it releases nutrients (N, P), gases (CO₂, CH₄), and
> dissolved carbon to the water column and atmosphere, so its mass is removed from the
> sediment layer.

#### 2c. Sediment gains from biomass (same timestep)

The turnover and burial outputs from step 2a are added to the sediment stocks:

| Gain | To |
|------|----|
| Turnover labile output | labile sediment stock |
| Turnover refractory output | refractory sediment stock |
| Burial labile/refractory/inorganic output | respective sediment stocks |

#### 2d. Sediment erosion (erosion track only)

The eroded sediment (total erosion depth minus the biomass already removed in 2a) is
removed from labile, refractory, and inorganic stocks in proportion to their current
relative sizes:

```
eroded_i = (stock_i / total_sediment) × (erosion_cm − bio_eroded_cm)   for each stock i
```

#### 2e. Layer depth update

The layer's bottom is fixed. The top is recomputed from the net change in sediment and
biomass lengths:

```
new_top = old_top − bio_delta − sed_delta
```

where `bio_delta` is the length of eroded biomass (negative when eroded) and `sed_delta`
is the net change in total sediment length (negative when material was lost). When material
is lost the top **sinks deeper** (increases), shrinking the layer from the top.

The top is clamped: `new_top ≤ bottom` (layer cannot have negative thickness).

#### 2f. Biomass remake

Biomass in the layer is recomputed from scratch using the external surface concentration
`R₀` and the new layer thickness:

```
B_layer = ∫[new_top → new_bottom] R₀ × e^(−k1 × z) dz
```

**Negative growth correction (model extension beyond M&B).** After remaking the biomass
from the distribution, the model checks whether the layer's biomass has decreased by more
than can be accounted for by erosion and burial alone:

```
ngrowth = B_original − (eroded + buried) − B_new
```

If `ngrowth > 0`, the layer contained more biomass than the distribution now says it should,
and that excess was not physically removed. The most common cause is the externally-supplied
surface concentration `R₀` being **lower** this timestep than last — fewer plants at the
surface means the exponential distribution produces less biomass at every depth, so this
layer's roots have partially died back.

The dead root mass cannot disappear; it is converted to sediment in the same proportions as
any dead plant material:

```
add ngrowth × (1−k3) × fl  →  labile sediment  (easily decomposed organic fraction)
add ngrowth × (1−k3) × fc  →  refractory sediment
add ngrowth × k3            →  inorganic sediment (ash)
```

This mechanism is **not present in Morris & Bowden (1986)** — it is a deliberate extension
to handle the case of plant community decline. In M&B, biomass is driven by fixed turnover
rates and assumed to remain stationary or grow; biomass dieback driven by a falling `R₀`
input is an additional scenario handled here implicitly through the distribution remake.
There is no explicit dieback rate parameter (e.g. a `kd`); the magnitude of die-back is
determined entirely by the change in the external `top` (R₀) input between timesteps.

---

### Stage 3 — New top layer (first sub-step only)

A new layer is created to represent this timestep's surface deposit. It is always placed at
depths `(0, dep + litter_length)`.

#### 3a. Litter

Above-ground plant material (leaves, stems) falls onto the marsh surface each timestep.
The amount is computed from the pre-computation biomass snapshot (Stage 1):

```
litter_total   = total_biomass × wa_to_rl × b × Δt   [g]
litter_labile  = litter_total × fl                    [g]
litter_refrac  = litter_total × fc                    [g]
litter_inorg   = 0                                    (litter is entirely organic)
```

`b = 1` (balanced, the default) means all locally produced litter stays on the cell.
`b < 1` means net export; `b > 1` means net import from adjacent cells.

Litter occupies physical space. Its length contribution:

```
litter_length = (litter_labile + litter_refrac) / bo / sa   [cm]
```

#### 3b. New layer depth and stock allocation

```
new_dep = dep + litter_length   [cm]
```

The new layer at `(0, new_dep)` contains:

| Component | Formula | Notes |
|-----------|---------|-------|
| Biomass | ∫₀^dep R₀ × e^(−k1×z) dz | Roots grow into deposited sediment, not into loose litter |
| Dep. sediment labile | (dep − bio.length) × fo × fl / bo / sa | Deposited sediment minus root volume, labile fraction |
| Dep. sediment refractory | (dep − bio.length) × fo × fc / bo / sa | Refractory fraction |
| Dep. sediment inorganic | (dep − bio.length) × fi / bi / sa | Inorganic fraction |
| **Litter labile** | **litter\_total × fl** | Added to sediment stocks |
| **Litter refractory** | **litter\_total × fc** | Added to sediment stocks |

All stock lengths sum exactly to `new_dep`:

```
bio.length + sed_labile.length + sed_refrac.length + sed_inorg.length = dep + litter_length
```

#### 3c. Elevation and coordinate update

All existing layers are shifted downward so that the bottom of the new top layer aligns
with the top of the previously-shallowest layer (no gaps in the sediment column):

```
shift = existing_top_layer.top − new_dep
layers[i].depths = (depths[0] − shift, depths[1] − shift)   for all existing layers
```

The cell surface elevation is updated:

```
elevation_change = −shift   (per sub-step; accumulated across sub-steps)
cell.elevation   = old_elevation + elevation_change
```

A positive `shift` means existing layers moved deeper (surface sank → elevation decreased).
A negative `shift` means existing layers moved shallower (surface rose → elevation increased).

---

## Summary Table

| What | From | To | When | Sign |
|------|------|----|------|------|
| Labile decomposition | labile sediment (each layer) | atmosphere / water column | every layer, every timestep | loss |
| Inorganic ash uptake | inorganic sediment (each layer) | above-ground production | every layer, every timestep | loss |
| Biomass turnover (labile) | biomass (each layer) | labile sediment (same layer) | every layer, every timestep | internal transfer |
| Biomass turnover (refractory) | biomass (each layer) | refractory sediment (same layer) | every layer, every timestep | internal transfer |
| Biomass burial | biomass at/below rd | labile/refractory/inorganic sediment (same layer) | deposition only | internal transfer |
| Biomass erosion | biomass in eroded zone | lost from system | erosion only | loss |
| Sediment erosion | labile/refractory/inorganic (top layers) | lost from system | erosion only | loss |
| Negative growth | biomass surplus | labile/refractory/inorganic sediment (same layer) | when biomass decreases beyond erosion/burial | internal transfer |
| Deposited sediment | external | labile/refractory/inorganic (new top layer) | deposition, every timestep | gain |
| Litter | above-ground production | labile/refractory (new top layer) | every timestep (scales with b) | gain |

---

## What Does Not Change

- **Layer bottoms** are fixed for the lifetime of a layer.
- **Refractory sediment** is not affected by decomposition or ash uptake — it changes only
  through erosion, burial inputs, turnover inputs, or negative growth.
- **Inorganic sediment** receives no litter (litter is entirely organic).
- The **new top layer** is not present at the start of the timestep — it is created during
  Stage 3 and represents only the material deposited or accumulated in this timestep.

---

## Model Limitations and Assumptions

1. **Not a closed system.** Turnover is a net gain (new growth assumed to instantly replace
   dead roots). Labile decomposition and ash uptake are net losses. Mass is not conserved.
2. **Discrete time.** The compute order above can affect results. Sub-steps reduce but do not
   eliminate this sensitivity.
3. **No horizontal variation.** Each layer is spatially homogeneous; stocks are not
   distributed within it.
4. **Root depth is fixed at `rd`.** Roots always grow to `rd` regardless of plant age or
   biomass level.
5. **Erosion creates an empty (zero-depth) layer.** When `dep ≤ 0`, Stage 3 still runs but
   creates a layer of `(0, 0 + litter_length)` at the surface. This is a deliberate design
   choice to make it unambiguous over which timesteps erosion occurred.
