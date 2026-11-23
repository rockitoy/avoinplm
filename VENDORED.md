# Vendored modules

These OCA modules are not yet released by the Odoo Community Association for Odoo 20.0.
This repository contains Odoo 20 ports with only the changes needed for Odoo 20. Original
authors, copyright notices and licenses are kept. Do not add features here: RockIT
changes live in the separate `rockit_*` modules. The copies will be replaced by the
official OCA 20.0 releases when they exist.

| Module | Source | Commit | License | Authors |
|---|---|---|---|---|
| `product_variant_default_code` (20.0.1.0.0, port) | [OCA/product-variant 19.0](https://github.com/OCA/product-variant/tree/19.0/product_variant_default_code) | `11d1c81e1521ce75437ab801bb608fc250433366` | AGPL-3 | AvancOSC, Shine IT, Tecnativa, Akretion, Odoo Community Association (OCA); see `product_variant_default_code/readme/CONTRIBUTORS.md` |
| `mrp_bom_version` (20.0.1.0.0, port) | [OCA/manufacture 18.0](https://github.com/OCA/manufacture/tree/18.0/mrp_bom_version) (no 19.0/20.0 version yet) | `4e794d05ffeb8f14ff4895bce9747a77b28fe8cb` | AGPL-3 | OdooMRP team, AvanzOSC, Serv. Tecnol. Avanzados - Pedro M. Baeza, Odoo Community Association (OCA); see `mrp_bom_version/readme/CONTRIBUTORS.md` |

## product_variant_default_code: changes for Odoo 20

- `__manifest__.py`: version `19.0.1.0.0` → `20.0.1.0.0`.
- `models/product.py`: `ir.config_parameter.get_param()` → `get_str()` / `get_bool()`
  (Odoo 20 removed `get_param`).
- `tests/test_variant_default_code.py`: `set_param()` → `set_bool()`.
- `views/product_view.xml`: removed the inheritance of `product.product_variant_easy_edit_view`
  (the view does not exist in Odoo 20).

Installing into an existing database: run `tools/pre_install_product_variant_default_code.sql`
first. Otherwise the install recomputes and overwrites every existing internal reference
(tested on a copy of a demo database: 129 changed codes without the script, 0 with it).

## mrp_bom_version: changes for Odoo 20

- `__manifest__.py`: version `18.0.1.0.0` → `20.0.1.0.0`.
- `models/mrp_bom.py`: `get_param()` → `get_bool()` (`button_draft`, `_copy_bom`); BoM line
  `product_uom_id` → `uom_id`; the `consumption` field removed in Odoo 20 was removed from
  the field list and from `get_view`.
- `views/mrp_bom_view.xml`: `uom_id` attribute; removed the `consumption` attribute block.
- `views/res_config_view.xml`: anchor `<setting id="mrp_lock" position="after">`.
- `security/*.xml`: removed the `category_id` line (Odoo 20 uses `privilege_id`).
- `tests/`: `set_param()` → `set_bool()`, `TransactionCase` (Odoo 20's `BaseCommon` runs
  tests without MRP rights), own test products instead of demo references.

Behaviour to know: a new BoM is a *draft* and archived (not used before activation) by
default, unless the setting *Active draft* (`mrp_bom_version.active_draft`) is on.
`rockit_plm_eco` activates the draft BoMs of a PLM item when its revision is released, and
the BoM versions of an ECO when the ECO takes effect. Installing the module marks existing
active BoMs as *active*.
