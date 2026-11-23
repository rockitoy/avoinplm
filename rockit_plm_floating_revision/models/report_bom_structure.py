# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.api import NewId


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    @api.model
    def _get_bom_data(self, bom, warehouse, product=False, line_qty=False, bom_line=False,
                      level=0, parent_bom=False, parent_product=False, index=0,
                      product_info=False, ignore_stock=False, simulated_leaves_per_workcenter=False):
        # BoMs with attribute-matched lines are virtualised by mrp_bom_attribute_match
        # (resolved by the component family bridge); fixed floating lines are handled here
        virtual = (
            isinstance(bom.id, int)
            and product
            and not bom._plm_resolved_by_attribute_match()
            and bom._plm_has_floating_lines()
        )
        if virtual:
            bom = bom._plm_prepare_floating_bom(bom, product)
        data = super()._get_bom_data(
            bom, warehouse, product=product, line_qty=line_qty, bom_line=bom_line, level=level,
            parent_bom=parent_bom, parent_product=parent_product, index=index,
            product_info=product_info, ignore_stock=ignore_stock,
            simulated_leaves_per_workcenter=simulated_leaves_per_workcenter,
        )
        if virtual:
            for component in data.get("components", []):
                for key, value in component.items():
                    if isinstance(value, NewId):
                        component[key] = value.origin
        for component in data.get("components", []):
            prod = self.env["product.product"].browse(component.get("product_id") or [])
            component["plm_revision"] = prod.plm_revision if prod else False
        return data
