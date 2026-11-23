# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PLM variant internal references",
    "summary": "Internal references without the revision: PLM items keep their code over "
    "revisions, variant families get per-variant codes from product_variant_default_code",
    "version": "20.0.1.1.0",
    "development_status": "Beta",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "website": "https://github.com/rockitoy/avoinplm",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": [
        "plm_auto_internalref",
        "product_variant_default_code",
        "rockit_plm_floating_revision",
    ],
    "data": ["views/plm_component_views.xml"],
    "installable": True,
}
