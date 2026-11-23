# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PLM floating revisions in manufacturing",
    "summary": "BoM lines use the effective released PLM revision at use time, superseded "
    "revisions are used up first; revision data is carried over to new revisions; "
    "revision column on products, BoM lines, MO components, purchase and stock moves",
    "version": "20.0.2.0.0",
    "development_status": "Beta",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "website": "https://github.com/rockitoy/avoinplm",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": [
        "plm",
        "plm_web_revision",
        "purchase_stock",
        "mrp_account",
    ],
    "data": [
        "security/ir.access.csv",
        "views/plm_release_impact_views.xml",
        "views/product_views.xml",
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_move_views.xml",
    ],
    "installable": True,
}
