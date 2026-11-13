# 31. Deferral extension, non-recoverable parts, article classes

## A. Single extension of a deferral (RIE)

**Account: `camo`**

The MEL allows, for categories **B and C**, only **one** extension of the rectification interval (RIE). It is approved by the CAMO **before the limit**, for a duration not exceeding the initial interval, and the authority is informed.

1. Menu **Defects & deferrals** → **DEF-...-0002** (F-HDMC, cabin lighting, cat. C, limit D+10).
2. **Extend the limit (RIE)** frame: new limit (date) D+20, RIE reference `RIE-2026-001`, justification `Ampoule en commande, livraison J+12`. Tick "authority informed" if done. Password → **Approve and sign the extension**.

**Result**: the new limit is used everywhere (due items, planning, dashboard). The record displays the initial limit, the approver and the reference, and a "Deferral extension (RIE)" signature is added.

**Checks**:

| Case | Result |
|---|---|
| New limit beyond D+20 (initial interval 10 d) | Refused: "Extension (date) greater than the initial interval" |
| Adding a criterion absent from the initial deferral (e.g. FH) | Refused |
| Second extension | Refused: "a second extension is not allowed" |
| Limit already reached | Refused: "the extension must be approved before the limit" |
| Category A, D or outside the MEL | Refused |
| Non-CAMO user (e.g. `b2`) | Frame not displayed, action refused |

## B. Non-recoverable part: scrapping

**Account: `magasin`**

A non-recoverable part (LLP at its limit, unrepairable, damaged, insufficient traceability) must be **mutilated** so that it can never return to the supply chain (145.A.42(d), M.A.504(d)).

1. Menu **Components** → a removed component, with the status "Unserviceable" or "Quarantine".
2. **Scrap (non-recoverable part)** frame: date, reason, mutilation method (`Découpe`), witness (`Isabelle GARNIER (qualité)`), destruction certificate ref. Password → **Sign the final scrapping**.

**Result**: status **Scrapped**, final. The status can no longer change, neither through the screen, nor through the administration, nor through the API. Example in the demo: the rotor hub `DEMO-S3399`, at its life limit.

An installed or reserved part cannot be scrapped.

## C. Article classes (145.A.42(a))

**Account: `magasin`**

Each P/N reference has a **class**, which determines the document required at receipt:

| Class | Accepted document | Demo example |
|---|---|---|
| Component | EASA Form 1, FAA 8130-3, dual release, TCCA Form One | Engines, BTP, oil filter, magnetic plug |
| Standard part | Certificate of conformity (CoC), standard mandatory | O-ring `AS568-012` |
| Raw material | CoC, specification mandatory | Lockwire `MS20995C32` |
| Consumable | CoC | Oil, grease |

**Test**: menu **Receipt** → P/N `DEMO-350FLT-01` (filter, component) with a "Certificate of conformity" certificate → refused: "an authorised release certificate … is required". The same attempt with `DEMO-OIL-T2` (consumable) is accepted.

A serialised, rotable or life-limited reference is necessarily a component.
