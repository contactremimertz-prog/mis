# 17. Stores receipt and release certificates

**Account: `magasin`**

Every part enters AHMIS through **receipt**, with its release certificate.

## 1. Receiving a consumable

Menu **Receipt**:

- P/N `DEMO-OIL-T2` (turbine oil), batch no. `LOT-OIL-2701`, quantity `24`, location `MAG-PRINC`, expiry date in 2 years (mandatory for this article);
- certificate: type "Certificate of conformity", no. `COC-5521`, issuer `Distributeur agréé démo`, today's date;
- tick the **3 receiving inspections** → **Save**.

**Result**: the batch appears in **Consumables stock**, "Serviceable", with an incoming movement.

## 2. Receiving a serialised part

- P/N `DEMO-SG-150` (starter-generator), S/N `DEMO-G1700`, quantity 1, condition "Repaired", TSN `850`, CSN `2400`, TSO `0`, CSO `0`;
- certificate: EASA Form 1, no. `F1-778`, issuer `Atelier équipements agréé`, approval no. `FR.145.DEMO-Y`, status "Repaired";
- 3 inspections ticked → **Save**.

**Result**: the component record opens, with its accepted certificate. The part can be issued and installed.

## 3. Non-compliant receipt → automatic quarantine

Repeat a receipt (S/N `DEMO-G1701`) **without ticking** "Certificate complete, signed, approved issuer".

**Result**: "placed in QUARANTINE". The part is stored in `QUAR`, its certificate is marked rejected, and it can be neither issued nor installed.

## Entry checks

- S/N mandatory for a serialised part; quantity 1.
- A P/N + S/N pair already known is refused: "duplicate or suspected part".
- Expiry date mandatory for articles with a limited shelf life.
- Future certificate date refused.
- **Article class** (P/N record, 145.A.42): a **component** requires an authorised release certificate (EASA Form 1, FAA 8130-3, dual release, TCCA Form One). A certificate of conformity (CoC) is accepted only for a standard part, a raw material or a consumable. See tutorial 31.

## Certificates

Menu **Release certificates**: all the Form 1s, 8130-3s and CoCs. The certificate scan can be attached ("Certificate scan" field).
