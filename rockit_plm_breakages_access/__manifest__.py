# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PLM breakages: no access error for non-PLM users",
    "summary": "Breakage counters on BoMs, BoM lines, MOs and products are 0 for users "
    "without access to PLM breakages instead of raising an access error",
    "version": "20.0.1.0.0",
    "development_status": "Beta",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "website": "https://github.com/rockitoy/avoinplm",
    "author": "RockIT Oy",
    "license": "AGPL-3",
    "depends": ["plm_breakages"],
    "auto_install": True,
    "installable": True,
}
