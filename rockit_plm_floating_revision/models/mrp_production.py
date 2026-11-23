# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.api import NewId

from .mrp_bom import DATE_CTX, LOCATION_CTX


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    product_revision = fields.Char(related="product_id.plm_revision", string="Revision")

    def _get_moves_raw_values(self):
        # resolve floating revisions at the MO's planned start, in its source location
        moves = []
        for production in self:
            moves += super(MrpProduction, production.with_context(**{
                DATE_CTX: production.date_start,
                LOCATION_CTX: production.location_src_id.id,
            }))._get_moves_raw_values()
        return moves

    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        if bom_line and isinstance(bom_line.id, NewId):
            # a line split over revisions by mrp.bom.explode: keep the real BoM line
            bom_line = bom_line._plm_real_line()
        return super()._get_move_raw_values(product, product_uom_qty, product_uom,
                                            operation_id=operation_id, bom_line=bom_line)
