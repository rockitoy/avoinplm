# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PLM floating revisions for attribute-matched BoM lines and component families",
    "summary": "Bridge between rockit_plm_floating_revision (AvoinPLM) and the configurator "
    "modules: attribute-matched lines and component families float to the effective "
    "PLM revision too",
    "version": "20.0.1.0.0",
    "development_status": "Beta",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "website": "https://github.com/rockitoy/avoinplm",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": [
        "rockit_plm_floating_revision",
        "rockit_mrp_bom_component_family",
        "rockit_bom_attribute_match_dynamic",
    ],
    "data": [],
    "auto_install": True,
    "installable": True,
}
