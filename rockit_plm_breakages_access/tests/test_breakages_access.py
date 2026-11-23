# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestBreakagesAccess(TransactionCase):
    def test_mrp_user_without_plm_rights(self):
        user = new_test_user(self.env, login="brk_mrp_user", groups="mrp.group_mrp_user")
        self.assertFalse(self.env["plm.breakages"].with_user(user).has_access("read"))
        product = self.env["product.product"].create({"name": "BRK Product"})
        bom = self.env["mrp.bom"].create({"product_tmpl_id": product.product_tmpl_id.id, "bom_line_ids": [
            (0, 0, {"product_id": self.env["product.product"].create({"name": "BRK Comp"}).id})]})
        bom = bom.with_user(user)
        self.assertEqual(bom.breakages_count, 0)
        self.assertEqual(bom.bom_line_ids.breakages_count, 0)
        self.assertEqual(product.with_user(user).breakages_count, 0)

    def test_plm_user_counts(self):
        product = self.env["product.product"].create({"name": "BRK Product 2"})
        self.env["plm.breakages"].create({"product_id": product.id})
        self.assertEqual(product.breakages_count, 1)
