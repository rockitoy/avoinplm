# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    product_revision = fields.Char(related="product_id.plm_revision", string="Revision")

    def _get_orderpoints_to_update(self):
        # stock of a superseded revision counts in the current revision's rules
        orderpoints = super()._get_orderpoints_to_update()
        newer = self.product_id._plm_newer_counterparts()
        if newer:
            warehouses = (self.location_id | self.location_dest_id).warehouse_id
            domain = [("product_id", "in", newer.ids)]
            if warehouses:
                domain.append(("warehouse_id", "in", warehouses.ids))
            orderpoints |= self.env["stock.warehouse.orderpoint"].sudo().search(domain)
        return orderpoints


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_revision = fields.Char(related="product_id.plm_revision", string="Revision")
