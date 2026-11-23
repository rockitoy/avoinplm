**Status: Beta** – tested in a demo environment, not yet in customer production.

Glue module between AvoinPLM (*rockit_plm_floating_revision*) and the configurator
modules of [odoo-konfiguraattori](https://github.com/rockitoy/odoo-konfiguraattori)
(*mrp_bom_attribute_match*, *rockit_bom_attribute_match_dynamic*,
*rockit_mrp_bom_component_family*). Installed automatically when both sides are installed.

- **Attribute-matched lines** (*Component (product template)*) and **component
  families** use the PLM revision that is released and effective at use time, and use up
  superseded revisions first, like fixed lines do.
- Fixed floating lines in BoMs that *mrp_bom_attribute_match* virtualises (BoM cost,
  BoM structure report) are resolved to the effective revision.
- The *Revision* column shows `↻ <rev>` for attribute-matched lines and `↻` for lines with
  component families (the item is chosen per produced variant).

Without this module *rockit_plm_floating_revision* works on fixed BoM lines only.
