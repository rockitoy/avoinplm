# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plm_eco_id = fields.Many2one("plm.eco", "ECO", copy=False, readonly=True,
                                 help="Engineering change order that created this revision")

    def _plm_on_release(self):
        """Apply the ECO effectivity policy, activate the revision's BoMs, close the ECO."""
        self.ensure_one()
        eco = self.plm_eco_id
        if eco:
            effective_date, phase_out = eco._effectivity_values()
            self.revision_effective_date = effective_date
            older = self._plm_revisions().filtered(
                lambda r: r.engineering_revision < self.engineering_revision)
            older.write({"revision_phase_out": phase_out})
        res = super()._plm_on_release()
        draft_boms = self.env["mrp.bom"].with_context(active_test=False).search([
            ("product_tmpl_id", "=", self.id), ("state", "=", "draft"), ("plm_eco_id", "=", False)])
        draft_boms.button_activate()
        if eco:
            eco._on_revision_released(self)
        return res
