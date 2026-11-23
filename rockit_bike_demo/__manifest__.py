# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "RockIT bicycle demo (AvoinPLM, fictional data)",
    "version": "20.0.2.5.0",
    "development_status": "Beta",
    "summary": "Fictional demo company (Pyöräpaja Demo Oy): configurable bicycle in the "
    "webshop, two-level attribute BoM, paint shop, MTO purchasing, vendors, invoicing and "
    "a PLM change request",
    "author": "RockIT Oy",
    "website": "https://github.com/rockitoy/avoinplm",
    "license": "AGPL-3",
    "category": "Manufacturing",
    "depends": [
        "l10n_fi",
        "website_sale",
        "website_sale_stock",
        "sale_mrp",
        "sale_stock",
        "purchase_stock",
        "purchase_mrp",
        "mrp_account",
        "plm",
        "activity_validation",
        "rockit_bom_attribute_match_dynamic",
        "rockit_mrp_bom_component_family",
        "rockit_plm_eco",
        "rockit_plm_variant_default_code",
    ],
    "data": [
        "data/base_data.xml",
        "data/attributes.xml",
        "data/products.xml",
        "data/export_templates.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
