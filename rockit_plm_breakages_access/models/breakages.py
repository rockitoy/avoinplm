# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

# plm_breakages computes the counters as the user (compute_sudo=False): a user without
# PLM rights (e.g. a production operator) gets an access error when opening a BoM or an
# MO. Show 0 to them instead.


def _no_access(records):
    if records.env["plm.breakages"].has_access("read"):
        return False
    for record in records:
        record.breakages_count = 0
    return True


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _compute_breakages_count(self):
        if not _no_access(self):
            return super()._compute_breakages_count()


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    def _compute_breakages_count(self):
        if not _no_access(self):
            return super()._compute_breakages_count()


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _compute_breakages_count(self):
        if not _no_access(self):
            return super()._compute_breakages_count()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_breakages_count(self):
        if not _no_access(self):
            return super()._compute_breakages_count()
