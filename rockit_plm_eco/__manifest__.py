# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PLM engineering change orders (ECO)",
    "summary": "ECR → ECO → revisions → effectivity: affected items, effectivity policy "
    "applied on release, impact analysis, BoM versions, ECO closes when released",
    "version": "20.0.1.1.0",
    "development_status": "Beta",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "website": "https://github.com/rockitoy/avoinplm",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": [
        "activity_validation",
        "mrp_bom_version",
        "rockit_plm_floating_revision",
    ],
    "data": [
        "security/ir.access.csv",
        "data/plm_eco_data.xml",
        "views/plm_eco_views.xml",
        "views/mail_activity_views.xml",
        "views/product_views.xml",
    ],
    "installable": True,
}
