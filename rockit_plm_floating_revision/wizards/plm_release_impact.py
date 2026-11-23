# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

MO_OPEN_STATES = ("draft", "confirmed")
RFQ_STATES = ("draft", "sent", "to approve")


class PlmReleaseImpact(models.TransientModel):
    _name = "plm.release.impact"
    _description = "Open orders affected by a PLM revision"

    product_tmpl_id = fields.Many2one("product.template", "Revision", required=True, readonly=True)
    line_ids = fields.One2many("plm.release.impact.line", "wizard_id", "Affected documents")
    line_count = fields.Integer(compute="_compute_line_count")

    @api.depends("line_ids")
    def _compute_line_count(self):
        for wizard in self:
            wizard.line_count = len(wizard.line_ids)

    @api.model
    def _plm_open_for(self, template):
        wizard = self.create({"product_tmpl_id": template.id})
        wizard.line_ids = [(0, 0, vals) for vals in template._plm_release_impact()]
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Open orders on older revisions"),
            "res_model": self._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda line: line.update and line.can_update)
        for line in lines:
            line._apply()
        if lines:
            self.product_tmpl_id.message_post(body=self.env._(
                "Updated %(count)s open order line(s) to revision %(rev)s: %(docs)s",
                count=len(lines), rev=self.product_tmpl_id.engineering_revision,
                docs=", ".join(sorted(set(lines.mapped("document")))),
            ))
        return {"type": "ir.actions.act_window_close"}


class PlmReleaseImpactLine(models.TransientModel):
    _name = "plm.release.impact.line"
    _description = "Open order line on an older PLM revision"
    _order = "kind, date, id"

    wizard_id = fields.Many2one("plm.release.impact", required=True, ondelete="cascade")
    kind = fields.Selection([
        ("mo", "Manufacturing order component (not started)"),
        ("mo_product", "Manufacturing order producing the item"),
        ("rfq", "Request for quotation"),
        ("po", "Confirmed purchase order"),
    ], required=True, readonly=True)
    document = fields.Char(readonly=True)
    date = fields.Datetime(readonly=True)
    move_id = fields.Many2one("stock.move", readonly=True)
    production_id = fields.Many2one("mrp.production", readonly=True)
    purchase_line_id = fields.Many2one("purchase.order.line", readonly=True)
    product_id = fields.Many2one("product.product", "Product now", readonly=True)
    revision = fields.Char(related="product_id.plm_revision", string="Rev. now")
    quantity = fields.Float(digits="Product Unit", readonly=True)
    keep_qty = fields.Float("Keep on old revision", digits="Product Unit", readonly=True)
    new_product_id = fields.Many2one("product.product", "Proposed", readonly=True)
    new_revision = fields.Char(related="new_product_id.plm_revision", string="Rev. proposed")
    can_update = fields.Boolean(readonly=True)
    update = fields.Boolean()
    note = fields.Char(readonly=True)

    def _apply(self):
        self.ensure_one()
        if self.kind == "mo":
            self._apply_move()
        elif self.kind == "rfq":
            self._apply_rfq_line()
        elif self.kind == "mo_product":
            self._apply_production()

    def _apply_production(self):
        production = self.production_id
        if production.state != "draft":
            return
        product = self.new_product_id
        bom = self.env["mrp.bom"]._bom_find(product, company_id=production.company_id.id)[product]
        production.write({"product_id": product.id, "bom_id": bom.id or production.bom_id.id})

    def _apply_move(self):
        move = self.move_id
        if move.state in ("done", "cancel") or move.raw_material_production_id.state not in MO_OPEN_STATES:
            return
        production = move.raw_material_production_id
        move._do_unreserve()
        switch_qty = move.product_uom_qty - self.keep_qty
        if move.uom_id.compare(switch_qty, 0.0) <= 0:
            return
        if move.uom_id.compare(self.keep_qty, 0.0) <= 0:
            move.product_id = self.new_product_id
        else:
            vals_list = move._split(switch_qty)
            for vals in vals_list:
                vals["product_id"] = self.new_product_id.id
            self.env["stock.move"].create(vals_list)._action_confirm(merge=False)
        if production.state == "confirmed":
            production.action_assign()

    def _apply_rfq_line(self):
        line = self.purchase_line_id
        if line.order_id.state not in RFQ_STATES:
            return
        old_orderpoint = line.orderpoint_id
        vals = {"product_id": self.new_product_id.id}
        if old_orderpoint:
            vals["orderpoint_id"] = self.env["stock.warehouse.orderpoint"].search([
                ("product_id", "=", self.new_product_id.id),
                ("location_id", "=", old_orderpoint.location_id.id),
            ], limit=1).id
        qty, date_planned = line.product_qty, line.date_planned
        line.write(vals)
        # price, vendor lead time and description of the new revision
        # (the compute does not depend on product_id)
        line._compute_price_unit_and_date_planned_and_name()
        line.write({"product_qty": qty, "date_planned": date_planned})
