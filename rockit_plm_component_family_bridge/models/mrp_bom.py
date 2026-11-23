# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

from odoo.addons.rockit_plm_floating_revision.models.mrp_bom import NO_FLOAT_CTX


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    @api.depends("component_template_id", "component_family_ids")
    def _compute_component_revision(self):
        return super()._compute_component_revision()

    def _plm_component_template(self):
        self.ensure_one()
        return self.component_template_id or super()._plm_component_template()

    def _plm_floating_revision_label(self, template):
        # with component families the item (and so its revision) is chosen per variant
        if self.component_family_ids:
            return "↻"
        return super()._plm_floating_revision_label(template)

    def _plm_fixed_floating(self):
        return not self.component_template_id and super()._plm_fixed_floating()


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _plm_resolved_by_attribute_match(self):
        return any(self.bom_line_ids.mapped("component_template_id"))

    # attribute-matched lines (mrp_bom_attribute_match entry point)
    def _get_component_template_product(self, bom_line, bom_product_id, line_product_id):
        product = super()._get_component_template_product(bom_line, bom_product_id, line_product_id)
        if self.env.context.get(NO_FLOAT_CTX) or not bom_line.component_template_id:
            return product
        return self._plm_resolve_one(bom_line, product)

    # fixed lines in BoMs virtualised by mrp_bom_attribute_match (BoM cost, structure report)
    def _prepare_dynamic_bom(self, bom, product):
        bom = super()._prepare_dynamic_bom(bom, product)
        return self._plm_prepare_floating_bom(bom, product)
