# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .test_floating_revision import FloatingRevisionCommon, _png


@tagged("post_install", "-at_install")
class TestReleaseAccess(FloatingRevisionCommon):
    """A PLM engineer (OdooPLM integration + release user, may create products) who is
    not an inventory, purchase or website administrator revises and releases an item."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groups = (cls.env.ref("base.group_user") | cls.env.ref("plm.group_plm_integration_user")
                  | cls.env.ref("plm.group_plm_release_users") | cls.env.ref("product.group_product_manager"))
        cls.engineer = cls.env["res.users"].create({
            "name": "FR engineer", "login": "fr_engineer", "group_ids": [(6, 0, groups.ids)]})
        cls.designer = cls.env["res.users"].create({
            "name": "FR designer", "login": "fr_designer",
            "group_ids": [(6, 0, (groups - cls.env.ref("plm.group_plm_release_users")).ids)]})
        size_s = cls.frame.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "S")
        if "product_template_image_ids" in cls.frame._fields:
            cls.env["product.image"].create({"name": "FR S picture", "image_1920": _png("green"),
                                             "product_tmpl_id": cls.frame.id,
                                             "attribute_value_ids": [(6, 0, size_s.ids)]})

    def _revise_as(self, user, template):
        variant = template.with_user(user).product_variant_ids[:1]
        wizard = self.env["product.rev_wizard"].with_user(user).with_context(
            active_id=variant.id, active_model="product.product").create({"reviseDocument": False})
        wizard.action_create_new_revision_by_server()
        return template.with_user(user).get_next_version()

    def test_engineer_has_no_admin_rights(self):
        for xmlid in ("stock.group_stock_manager", "purchase.group_purchase_manager",
                      "purchase.group_purchase_user", "base.group_system"):
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                self.assertNotIn(group, self.engineer.all_group_ids, xmlid)

    def test_engineer_revises_and_releases(self):
        OP = self.env["stock.warehouse.orderpoint"].with_context(active_test=False)
        old_rules = OP.search([("product_id", "in", self.frame.product_variant_ids.ids)])
        self.assertEqual(len(old_rules), 2)
        rev1 = self._revise_as(self.engineer, self.frame)
        self.assertEqual(rev1.engineering_revision, 1)
        # vendor prices and images carried over to the new revision
        new_m = self.frame_m._plm_counterpart(rev1.sudo())
        sellers = rev1.sudo().seller_ids
        self.assertEqual(len(sellers), 2)
        self.assertEqual(sellers.filtered(lambda s: s.product_id == new_m).price, 90)
        if "product_template_image_ids" in rev1._fields:
            self.assertEqual(rev1.sudo().product_template_image_ids.mapped("name"), ["FR S picture"])
        # release as the engineer
        variant = rev1.with_user(self.engineer).product_variant_ids[:1]
        variant.action_confirm()
        variant.action_release()
        self.assertEqual(rev1.engineering_state, "released")
        self.assertEqual(self.frame.engineering_state, "obsoleted")
        # reordering rules moved to the new revision, old ones archived
        self.assertFalse(old_rules.filtered("active"))
        new_rules = OP.search([("product_id", "in", rev1.product_variant_ids.ids)])
        self.assertEqual(len(new_rules), 2)
        self.assertTrue(all(new_rules.mapped("active")))
        self.assertEqual(sorted(new_rules.mapped("product_max_qty")), [4, 4])
        self.assertEqual(new_rules.company_id, old_rules.company_id)

    def test_release_requires_release_group(self):
        rev1 = self._revise_as(self.designer, self.frame)
        variant = rev1.with_user(self.designer).product_variant_ids[:1]
        variant.action_confirm()
        with self.assertRaises(AccessError):
            variant.action_release()
        self.assertEqual(rev1.engineering_state, "confirmed")
        self.assertEqual(len(self.env["stock.warehouse.orderpoint"].search(
            [("product_id", "in", self.frame.product_variant_ids.ids)])), 2)
