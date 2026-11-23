# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.rockit_plm_floating_revision.tests import test_floating_revision as base


@tagged("post_install", "-at_install")
class TestFloatingRevisionAttributeMatch(base.TestFloatingRevision):
    """The whole floating revision suite again, with the frame on an attribute-matched
    (template) line instead of a fixed line."""

    allow_inherited_tests_method = True  # run the inherited tests in this class too

    @classmethod
    def _frame_line_vals(cls):
        return {"component_template_id": cls.frame.id, "product_qty": 1}

    def test_bridge_template_line_floats_per_variant(self):
        frame_s = self.frame.product_variant_ids - self.frame_m
        self._stock(frame_s, 1)
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        bike_s = self.assembly._create_product_variant(
            self.assembly.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "S"))
        mo = self.env["mrp.production"].create({"product_id": bike_s.id, "bom_id": self.bom.id, "product_qty": 2})
        mo.action_confirm()
        moves = mo.move_raw_ids.filtered(lambda m: m.product_id.engineering_code == "FR-FRAME")
        self.assertEqual(set(moves.product_id.mapped("default_code")), {"FR-FRAME-S"})
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 1), (1, 1)], "old S used up, then rev 1")
        line = self.bom.bom_line_ids.filtered("component_template_id")
        self.assertEqual(line.component_revision, "↻ 1")

    def test_bridge_component_family_line(self):
        line = self.bom.bom_line_ids.filtered("component_template_id")
        line.component_family_ids = [(6, 0, self.frame.ids)]
        self.env.invalidate_all()
        self.assertEqual(line.component_revision, "↻")
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        self.assertEqual(self._moves(self._mo(1), "FR-FRAME"), [(1, 1)])
