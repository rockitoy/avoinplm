# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import AccessError


class ProductProduct(models.Model):
    _inherit = "product.product"

    plm_revision = fields.Char(
        "Revision",
        compute="_compute_plm_revision",
        help="PLM engineering revision of this item (empty when not a PLM item).",
    )

    @api.depends("engineering_code", "engineering_revision")
    def _compute_plm_revision(self):
        for product in self:
            product.plm_revision = (
                str(product.engineering_revision) if product.engineering_code else False
            )

    def action_release(self):
        """The release button is shown to OdooPLM release users only; enforce the same on
        the server, since releasing moves reordering rules with elevated rights."""
        if not self.env["product.template"]._plm_can_release():
            raise AccessError(self.env._("Only OdooPLM release users can release a revision."))
        return super().action_release()

    def _plm_counterpart(self, template, create=False):
        """The variant of ``template`` (another revision) with the same attribute values."""
        self.ensure_one()
        if self.product_tmpl_id == template:
            return self
        if not template.attribute_line_ids:
            return template.product_variant_id
        values = self.product_template_attribute_value_ids.product_attribute_value_id
        combination = template.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.ptav_active and v.product_attribute_value_id in values
        )
        variant = template._get_variant_for_combination(combination)
        if not variant and create and not getattr(self.env.cr, "readonly", False):
            variant = template._create_product_variant(combination)
        return variant or self.browse()

    def _plm_newer_counterparts(self):
        """Variants of newer revisions matching these variants (existing ones only)."""
        result = self.browse()
        for product in self.filtered("engineering_code"):
            for template in product.product_tmpl_id._plm_revisions():
                if template.engineering_revision > product.engineering_revision:
                    result |= product._plm_counterpart(template)
        return result

    def _plm_update_family_orderpoints(self):
        """Recompute the stored "to order" of all rules of these items' revisions."""
        templates = self.env["product.template"]
        for product in self.filtered("engineering_code"):
            templates |= product.product_tmpl_id._plm_revisions()
        orderpoints = self.env["stock.warehouse.orderpoint"].sudo().search(
            [("product_id", "in", templates.product_variant_ids.ids)])
        if orderpoints:
            orderpoints.invalidate_recordset(["qty_to_order", "qty_forecast"])
            self.env.add_to_compute(orderpoints._fields["qty_to_order_computed"], orderpoints)

    def _plm_allocate(self, qty, at=None, location=None, create=False):
        """Split ``qty`` (in the product UoM) over the revisions of this item at ``at``:
        free stock of superseded "use up" revisions first (oldest first, counted in
        ``location`` and its children when given), the rest from the current revision.

        :return: list of (variant, qty)
        """
        self.ensure_one()
        if not self.engineering_code:
            return [(self, qty)]
        current, older = self.product_tmpl_id._plm_effective_revisions(at)
        allocation = []
        remaining = qty
        for template in older:
            variant = self._plm_counterpart(template)
            if not variant or not variant.is_storable:
                continue
            ctx_variant = variant.with_context(location=location) if location else variant
            free = max(ctx_variant.free_qty, 0.0)
            take = min(free, remaining)
            if variant.uom_id.compare(take, 0.0) > 0:
                allocation.append((variant, take))
                remaining -= take
            if variant.uom_id.compare(remaining, 0.0) <= 0:
                return allocation
        target = self._plm_counterpart(current, create=create) or self
        allocation.append((target, remaining))
        return allocation

    def action_plm_release_impact(self):
        self.ensure_one()
        return self.product_tmpl_id.action_plm_release_impact()

    def _get_bom_components_price(self, bom, boms_to_recompute=False, byproduct_bom=False):
        # BoM cost of fixed floating lines: use the revision effective now (as the BoM
        # structure report and manufacturing orders do), not the revision on the line.
        if bom and len(self) == 1 and not bom._plm_resolved_by_attribute_match() and bom._plm_has_floating_lines():
            bom = bom._plm_prepare_floating_bom(bom, self)
        return super()._get_bom_components_price(
            bom, boms_to_recompute=boms_to_recompute, byproduct_bom=byproduct_bom
        )
