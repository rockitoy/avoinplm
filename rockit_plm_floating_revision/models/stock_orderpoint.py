# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    plm_phase_in_qty = fields.Float(
        "Superseded revision stock",
        compute="_compute_plm_phase_in_qty",
        digits="Product Unit",
        help="Net forecast of superseded PLM revisions that are used up first "
        "(phase-out \"use up\"). It is counted in this rule's forecast: the current "
        "revision is only replenished for what the old stock does not cover, and a "
        "shortage of the old revision is replenished with the current one.",
    )

    def _compute_plm_phase_in_qty(self):
        quantities = self._plm_phase_in_quantities()
        for orderpoint in self:
            orderpoint.plm_phase_in_qty = quantities.get(orderpoint.id, 0.0)

    def _plm_phase_in_quantities(self):
        """{orderpoint id: forecasted quantity of older "use up" revisions of its product}

        Only for rules on the current effective revision. The older revision forecast
        (on hand + incoming - demand already allocated to it, at the rule location and
        horizon) is what floating BoM lines will still consume before the current one.
        """
        result = {}
        now = fields.Datetime.now()
        for orderpoint in self:
            product = orderpoint.product_id
            if not (product and orderpoint.location_id and product.engineering_code):
                continue
            current, older = product.product_tmpl_id._plm_effective_revisions(now)
            if product.product_tmpl_id != current or not older:
                continue
            context = orderpoint._get_product_context()
            qty = 0.0
            for template in older:
                old_variant = product._plm_counterpart(template)
                if not old_variant or not old_variant.is_storable:
                    continue
                # net forecast: a shortage of the old revision (demand already on it
                # that its stock does not cover) is replenished with the current one,
                # like SAP discontinuation passes requirements to the follow-up part
                forecast = old_variant.with_context(context).virtual_available
                qty += old_variant.uom_id._compute_quantity(forecast, product.uom_id)
            if qty:
                result[orderpoint.id] = qty
        return result

    def _get_orderpoint_action(self):
        res = super()._get_orderpoint_action()
        self._plm_merge_superseded_manual_orderpoints()
        return res

    @api.model
    def _plm_merge_superseded_manual_orderpoints(self):
        """The replenishment report creates manual rules for products with a negative
        forecast, also for superseded revisions. Their shortage is counted in the
        current revision's rule: replace them with a (manual) rule on the current
        revision at the same location."""
        # the report creates these rules as superuser for any inventory user: merge them
        # the same way (only manual rules of PLM items in the user's companies)
        Orderpoint = self.sudo().with_context(active_test=False)
        manual = Orderpoint.search([
            ("trigger", "=", "manual"), ("product_id.engineering_code", "!=", False),
            ("company_id", "in", self.env.companies.ids)])
        now = fields.Datetime.now()
        for orderpoint in manual:
            product = orderpoint.product_id
            current, older = product.product_tmpl_id._plm_effective_revisions(now)
            if product.product_tmpl_id == current or product.product_tmpl_id not in older:
                continue
            target = product._plm_counterpart(current, create=True)
            existing = Orderpoint.search([
                ("product_id", "=", target.id), ("location_id", "=", orderpoint.location_id.id)], limit=1)
            if existing:
                existing.active = True
            else:
                orderpoint.copy({"product_id": target.id, "trigger": "manual"})
            orderpoint.unlink()

    def _quantity_in_progress(self):
        res = super()._quantity_in_progress()
        for orderpoint_id, qty in self._plm_phase_in_quantities().items():
            res[orderpoint_id] = res.get(orderpoint_id, 0.0) + qty
        return res
