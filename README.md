# AvoinPLM – open PLM extensions for Odoo 20 Community

> **Status: Beta** – tested in a demo environment, not yet in customer production.
> **Tila: Beta** – testattu demoympäristössä, ei vielä asiakastuotannossa.

AvoinPLM ("open PLM") is a set of Odoo 20 Community Edition modules by
[RockIT Oy](https://rockit.fi) that build on [OmniaGit odooplm](https://github.com/OmniaGit/odooplm)
(branch `20.0`). They connect PLM revisions to manufacturing, purchasing and inventory:
BoM lines use the revision that is effective at use time, old revisions are used up
first, and engineering changes are run as ECR → ECO → revision → effectivity.

A demo company running these modules is at <https://plm.rockit.fi> (presentation on
request). Variant BoMs and component families for configurable products are in the
companion repository [odoo-konfiguraattori](https://github.com/rockitoy/odoo-konfiguraattori).

## Modules

| Module | Description |
|---|---|
| [rockit_plm_floating_revision](rockit_plm_floating_revision) | BoM lines float to the released, effective PLM revision at use time; superseded revisions are used up first; revision data is carried over to new revisions; phase-in replenishment; revision column on products, BoM lines, MOs, purchase and stock moves. |
| [rockit_plm_eco](rockit_plm_eco) | Engineering change orders: ECR → ECO, affected items, effectivity policy (use up old stock / immediately / from a date), impact analysis, BoM versions. |
| [rockit_plm_variant_default_code](rockit_plm_variant_default_code) | Internal references without the revision: PLM items keep their code over revisions; variant families get per-variant codes. |
| [rockit_plm_breakages_access](rockit_plm_breakages_access) | Users without PLM rights no longer get an access error from odooplm *plm_breakages* counters. |
| [rockit_plm_component_family_bridge](rockit_plm_component_family_bridge) | Bridge to odoo-konfiguraattori: attribute-matched BoM lines and component families float to the effective revision too. Auto-installed when both sides are installed. |
| [rockit_bike_demo](rockit_bike_demo) | **Fictional demo data** (bicycle workshop *Pyöräpaja Demo Oy*): configurable bicycle, two-level attribute BoM, paint shop, vendors, ECR ready for the ECO demo. Needs odoo-konfiguraattori too. Install only into an empty test database. |

Vendored OCA modules (not published by OCA for Odoo 20 yet; see [VENDORED.md](VENDORED.md)):

| Module | Source |
|---|---|
| [product_variant_default_code](product_variant_default_code) | OCA/product-variant 19.0, ported to 20.0 (used by *rockit_plm_variant_default_code*) |
| [mrp_bom_version](mrp_bom_version) | OCA/manufacture 18.0, ported to 20.0 (used by *rockit_plm_eco*) |

## Requirements

- Odoo 20.0 Community Edition.
- [OmniaGit odooplm](https://github.com/OmniaGit/odooplm), branch `20.0`. Used modules:
  `plm`, `plm_web_revision`, `plm_auto_internalref`, `activity_validation`,
  `plm_breakages` (only for *rockit_plm_breakages_access*). Tested with commit
  `d7f5a866791dad70e03dcbf0cf09e45d74b4f474`.
- Optional: [odoo-konfiguraattori](https://github.com/rockitoy/odoo-konfiguraattori) for
  attribute-matched BoM lines and component families (then the bridge module installs
  automatically).

## Installation

1. Put odooplm, this repository (and optionally odoo-konfiguraattori) in the
   `addons_path`.
2. **Existing database:** run [`tools/pre_install_product_variant_default_code.sql`](tools/pre_install_product_variant_default_code.sql)
   once *before* installing `product_variant_default_code` (directly or as a dependency).
   Otherwise the install recomputes and overwrites every existing internal reference.
   A new database does not need it.
3. Install in this order (dependencies are pulled in automatically, the order only makes
   the steps easier to follow):
   1. `rockit_plm_floating_revision`
   2. `rockit_plm_variant_default_code`
   3. `rockit_plm_eco`
   4. `rockit_plm_breakages_access` if you use `plm_breakages` (auto-installed with it)
   5. with odoo-konfiguraattori: `rockit_plm_component_family_bridge` (auto-installed
      on a new install; in a database where the modules are already installed, install it
      explicitly)
4. Demo (optional, empty test database only): `-i rockit_bike_demo` installs everything
   above plus the fictional bicycle demo data; it needs odoo-konfiguraattori in the
   addons path.
5. Run the tests: `odoo-bin -d <test db> -i <modules> --test-enable --test-tags
   /rockit_plm_floating_revision,/rockit_plm_eco,/rockit_plm_variant_default_code`.

## Known issues

- With *product_variant_default_code* (this repository) and *mrp_bom_attribute_match*
  (odoo-konfiguraattori) in the same database, one upstream test of
  *mrp_bom_attribute_match* (`test_check_product_with_component_change_allowed_no_variant`)
  errors: *product_variant_default_code* makes attribute names unique and the test creates
  a second attribute called "Size". This concerns that test only.

## User rights

| Task | Groups needed |
|---|---|
| Create a new revision | *OdooPLM - Integration User* + *Products: Create* |
| Release a revision | additionally *OdooPLM - PLM / Release Users* |
| ECR → ECO steps (odooplm change request activities) | additionally *Activity User* (odooplm activity_validation) |
| Apply *Open orders* changes to MOs and RFQs | Manufacturing / Purchase user rights |

No inventory, purchase or website administrator rights are needed to create or release a
revision.

## License

All modules are licensed under the **GNU Affero General Public License v3.0 or later**
(AGPL-3.0), see [LICENSE](LICENSE). The vendored OCA modules keep their original authors
and copyright notices. OmniaGit odooplm is a separate project: its repository is licensed
AGPL-3.0, and its modules declare `AGPL-3` or `LGPL-3` in their manifests (for example
`plm` and `plm_breakages` are LGPL-3, `activity_validation`, `plm_web_revision` and
`plm_auto_internalref` AGPL-3).

## Status and support

Beta. The modules have automated tests and run in the plm.rockit.fi demo, but have not yet
been used in a customer's production. Test them in a copy of your database first.

Issues and pull requests are welcome. Commercial implementation and support:
RockIT Oy, Tampere, Finland – <https://rockit.fi>, mikko.salmela@rockit.fi.

---

## Suomeksi

> **Beta – testattu demoympäristössä, ei vielä asiakastuotannossa.**

AvoinPLM on [RockIT Oy:n](https://rockit.fi) avoimen lähdekoodin laajennussarja Odoo 20
Community -versioon. Se rakentuu OmniaGitin [odooplm](https://github.com/OmniaGit/odooplm)-moduulien
päälle ja tuo tuotetiedon hallinnan (PLM) revisiot osaksi valmistusta, ostoa ja varastoa
samassa ERP-järjestelmässä:

- Osaluettelon rivi käyttää sitä revisiota, joka on julkaistu ja voimassa käyttöhetkellä
  ("kelluva revisio"). Vanhan revision varasto voidaan käyttää ensin loppuun.
- Uusi revisio perii variantit, tuotekoodit, toimittajahinnat, reitit, dokumentit ja
  osaluettelot. Täydennyssäännöt siirtyvät julkaisussa uudelle revisiolle.
- Muutokset kulkevat ketjuna muutospyyntö (ECR) → muutosmääräys (ECO) → revisio →
  voimaantulo: heti, päivämäärästä tai vanha varasto ensin. ECO:n vaikutusanalyysi
  näyttää käyttökohteet, varastot ja avoimet tilaukset.
- Revisio näkyy omana sarakkeenaan (SAP-tyyliin), ja tuotekoodi pysyy samana revisiosta
  toiseen.

Tuotekonfiguraattorin osat (varianttiosaluettelot ja komponenttiperheet) ovat erillisessä
[odoo-konfiguraattori](https://github.com/rockitoy/odoo-konfiguraattori)-repossa. Kun
molemmat ovat käytössä, siltamoduuli `rockit_plm_component_family_bridge` asentuu
automaattisesti.

`rockit_bike_demo` sisältää plm.rockit.fi-demon kuvitteellisen polkupyöräpajan
(*Pyöräpaja Demo Oy*) aineiston: konfiguroitava pyörä, kaksitasoinen osaluettelo,
maalaamo, toimittajat ja valmis muutospyyntö. Kaikki yritykset, henkilöt, nimikkeet ja
hinnat ovat keksittyjä. Asenna se vain tyhjään testikantaan; se tarvitsee myös
odoo-konfiguraattori-repon.

**Asennus:** Odoo 20 CE + odooplm (haara `20.0`) + tämä repo `addons_path`iin. Olemassa
olevassa kannassa aja ensin `tools/pre_install_product_variant_default_code.sql`, muuten
asennus kirjoittaa sisäiset viitteet uudelleen.

**Käyttöoikeudet:** revision luonti vaatii oikeudet *OdooPLM - Integration User* ja
*Products: Create* (Tuotteet: Luo), julkaisu lisäksi *OdooPLM - PLM / Release Users*, ja
ECR → ECO -vaiheet lisäksi *Activity User* (odooplm activity_validation). Varaston, oston
tai verkkosivujen ylläpito-oikeuksia ei tarvita.

**Lisenssi:** AGPL-3.0 tai uudempi. Vendoroidut OCA-moduulit säilyttävät alkuperäiset
tekijänsä.

**Demo:** <https://plm.rockit.fi> (esittely pyynnöstä). **Yhteys:** RockIT Oy, Tampere,
<https://rockit.fi>, mikko.salmela@rockit.fi.
