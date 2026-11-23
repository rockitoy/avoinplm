# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    plm_eco_id = fields.Many2one("plm.eco", "ECO", copy=False, readonly=True,
                                 help="Engineering change order that created this BoM version")
