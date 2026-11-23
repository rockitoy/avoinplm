# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPlmVariantDefaultCode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.size = cls.env["product.attribute"].create({"name": "VC Size", "create_variant": "dynamic",
            "value_ids": [(0, 0, {"name": "Small", "code": "S"}), (0, 0, {"name": "Medium", "code": "M"})]})
        cls.family = cls.env["product.template"].create({
            "name": "VC Frame", "type": "consu", "is_storable": True, "engineering_code": "VC-FRAME",
            "code_prefix": "VC-FRAME-",
            "attribute_line_ids": [(0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})],
        })
        for ptav in cls.family.attribute_line_ids.product_template_value_ids:
            cls.family._create_product_variant(ptav)
        cls.item = cls.env["product.template"].create({"name": "VC Fork", "type": "consu", "engineering_code": "VC-FORK"})
        (cls.family | cls.item).write({"engineering_state": "released"})

    def _new_revision(self, template):
        wizard = self.env["product.rev_wizard"].with_context(
            active_id=template.product_variant_ids[:1].id, active_model="product.product").create({"reviseDocument": False})
        wizard.action_create_new_revision_by_server()
        return template.get_next_version()

    def test_family_codes_from_mask(self):
        self.assertFalse(self.family.auto_default_code, "odooplm automatic code off for families")
        self.assertEqual(sorted(self.family.product_variant_ids.mapped("default_code")), ["VC-FRAME-M", "VC-FRAME-S"])
        rev1 = self._new_revision(self.family)
        self.assertEqual(rev1.engineering_revision, 1)
        self.assertEqual(rev1.code_prefix, "VC-FRAME-")
        self.assertEqual(sorted(rev1.product_variant_ids.mapped("default_code")), ["VC-FRAME-M", "VC-FRAME-S"])
        self.assertFalse(any(rev1.product_variant_ids.mapped("manual_code")), "codes still follow the mask")
        self.assertEqual(set(rev1.product_variant_ids.mapped("plm_revision")), {"1"})
        # changing a value code renames every revision consistently
        self.size.value_ids.filtered(lambda v: v.code == "M").code = "MED"
        self.assertIn("VC-FRAME-MED", rev1.product_variant_ids.mapped("default_code"))
        self.assertIn("VC-FRAME-MED", self.family.product_variant_ids.mapped("default_code"))

    def test_single_item_code_without_revision(self):
        self.assertEqual(self.item.product_variant_id.default_code, "VC-FORK")
        rev1 = self._new_revision(self.item)
        self.assertEqual(rev1.product_variant_id.default_code, "VC-FORK")
        self.assertEqual(rev1.product_variant_id.plm_revision, "1")

    def test_manual_code_is_carried(self):
        variant = self.family.product_variant_ids[:1]
        variant.default_code = "VC-SPECIAL"
        self.assertTrue(variant.manual_code)
        rev1 = self._new_revision(self.family)
        self.assertIn("VC-SPECIAL", rev1.product_variant_ids.mapped("default_code"))

    def test_revision_in_code_option(self):
        self.env["ir.config_parameter"].set_bool("rockit_plm_variant_default_code.revision_in_code", True)
        item = self.env["product.template"].create({"name": "VC Bolt", "type": "consu", "engineering_code": "VC-BOLT"})
        self.assertEqual(item.product_variant_id.default_code, "VC-BOLT_0")

    def test_engineering_parts_list(self):
        """Engineering Parts shows each variant's internal reference and attribute values and
        groups the latest revisions by family."""
        from lxml import etree
        arch = etree.fromstring(self.env["product.product"].get_view(
            self.env.ref("plm.plm_component_base_tree").id, "list")["arch"])
        names = [f.get("name") for f in arch.iter("field")]
        self.assertLess(names.index("default_code"), names.index("name"))
        self.assertIn("product_template_variant_value_ids", names)
        self.assertNotEqual(arch.xpath("//field[@name='default_code']")[0].get("optional"), "hide")
        search = etree.fromstring(self.env["product.product"].get_view(
            self.env.ref("plm.plm_component_base_search").id, "search")["arch"])
        self.assertTrue(search.xpath("//filter[@name='group_engineering_code']"))
        context = self.env.ref("plm.action_plm_component_base").context
        self.assertIn("search_default_group_engineering_code", context)
        rows = self.env["product.product"].search_read(
            [("engineering_code", "=", "VC-FRAME")], ["default_code", "product_template_variant_value_ids"])
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["product_template_variant_value_ids"] for r in rows))
        self.assertEqual(len({r["default_code"] for r in rows}), 2, "one internal reference per variant")
