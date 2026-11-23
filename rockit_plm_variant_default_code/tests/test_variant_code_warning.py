# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

PREFIX_MISSING = "Default Code can not be computed.\nReference Prefix is missing.\n"


@tagged("post_install", "-at_install")
class TestVariantCodeWarning(TransactionCase):
    """The "Default Code can not be computed" warning only when a code is missing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        Attr = cls.env["product.attribute"]
        cls.colour = Attr.create({"name": "VW Colour", "create_variant": "dynamic", "value_ids": [
            (0, 0, {"name": "Black", "code": "BLK"}), (0, 0, {"name": "White", "code": "WHT"})]})
        cls.size = Attr.create({"name": "VW Size", "create_variant": "always", "value_ids": [
            (0, 0, {"name": "Small", "code": "S"}), (0, 0, {"name": "Large", "code": "L"})]})

    def _template(self, attr, prefix=False, create_all=True):
        tmpl = self.env["product.template"].create({
            "name": f"VW {attr.name}", "type": "consu", "code_prefix": prefix,
            "attribute_line_ids": [(0, 0, {"attribute_id": attr.id, "value_ids": [(6, 0, attr.value_ids.ids)]})],
        })
        if create_all and attr.create_variant == "dynamic":
            for ptav in tmpl.attribute_line_ids.product_template_value_ids:
                tmpl._create_product_variant(ptav)
        return tmpl

    def _manual_codes(self, tmpl):
        for i, variant in enumerate(tmpl.product_variant_ids):
            variant.default_code = f"MAN-{i}"
        self.assertTrue(all(tmpl.product_variant_ids.mapped("manual_code")))

    def test_manual_codes_without_prefix_no_warning(self):
        """All variants coded by hand, all combinations created: nothing to compute."""
        for attr in (self.colour, self.size):
            tmpl = self._template(attr)
            self.assertEqual(tmpl.variant_default_code_error, PREFIX_MISSING, "no codes yet")
            self._manual_codes(tmpl)
            tmpl.invalidate_recordset(["variant_default_code_error"])
            self.assertFalse(tmpl.variant_default_code_error, attr.create_variant)

    def test_variant_without_code_warns(self):
        tmpl = self._template(self.size)
        self._manual_codes(tmpl)
        variant = tmpl.product_variant_ids[:1]
        variant.write({"default_code": False, "manual_code": True})
        tmpl.invalidate_recordset(["variant_default_code_error"])
        self.assertEqual(tmpl.variant_default_code_error, PREFIX_MISSING)
        variant.manual_code = False
        tmpl.code_prefix = "VW-"
        self.assertTrue(variant.default_code.startswith("VW-"))
        self.assertFalse(variant.manual_code)
        self.assertEqual(tmpl.product_variant_ids[1:].mapped("default_code"), ["MAN-1"], "manual codes kept")
        tmpl.invalidate_recordset(["variant_default_code_error"])
        self.assertFalse(tmpl.variant_default_code_error)

    def test_manual_variant_without_code_lists_variant(self):
        """Prefix and value codes fine, but a variant is manual with no code."""
        tmpl = self._template(self.size, prefix="VW-")
        variant = tmpl.product_variant_ids[:1]
        variant.write({"default_code": False, "manual_code": True})
        tmpl.invalidate_recordset(["variant_default_code_error"])
        self.assertIn("Variants without an internal reference", tmpl.variant_default_code_error)
        self.assertIn(variant.display_name, tmpl.variant_default_code_error)

    def test_dynamic_with_missing_combinations_needs_prefix(self):
        """New dynamic variants will be coded automatically, so the prefix is expected."""
        tmpl = self._template(self.colour, create_all=False)
        tmpl._create_product_variant(tmpl.attribute_line_ids.product_template_value_ids[:1])
        self._manual_codes(tmpl)
        tmpl.invalidate_recordset(["variant_default_code_error"])
        self.assertEqual(tmpl.variant_default_code_error, PREFIX_MISSING)
        tmpl.code_prefix = "VW-"
        tmpl.invalidate_recordset(["variant_default_code_error"])
        self.assertFalse(tmpl.variant_default_code_error)
        new = tmpl._create_product_variant(tmpl.attribute_line_ids.product_template_value_ids[1:2])
        self.assertEqual(new.default_code, "VW-WHT")
        self.assertFalse(new.manual_code)

    def test_error_per_template(self):
        """A value without code on one template does not leak into another template's text."""
        grey = self.env["product.attribute"].create({"name": "VW Grey", "create_variant": "always",
                                                     "value_ids": [(0, 0, {"name": "Grey"}), (0, 0, {"name": "Dark"})]})
        grey.value_ids.write({"code": ""})
        bad = self._template(grey, prefix="VB-")
        good = self._template(self.size, prefix="VG-")
        both = bad | good
        both.invalidate_recordset(["variant_default_code_error"])
        self.assertIn("Grey", bad.variant_default_code_error)
        self.assertFalse(good.variant_default_code_error)
