# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from math import prod

from odoo import api, models

REVISION_IN_CODE = "rockit_plm_variant_default_code.revision_in_code"


def _is_variant_family(template):
    """More than one possible variant: the code comes from the variant mask."""
    return any(len(line.value_ids) > 1 for line in template.attribute_line_ids)


class ProductProduct(models.Model):
    _inherit = "product.product"

    def compute_default_code(self, vals={}, objBrowse=None):  # noqa: B006 (odooplm signature)
        """odooplm automatic internal reference without the revision (the revision is
        its own field), and none for variant families (product_variant_default_code
        builds those from the attribute value codes)."""
        if self.env["ir.config_parameter"].sudo().get_bool(REVISION_IN_CODE):
            return super().compute_default_code(vals, objBrowse)
        template = self.env["product.template"]
        if objBrowse is not None:
            template = objBrowse if objBrowse._name == "product.template" else objBrowse.product_tmpl_id
        elif vals.get("product_tmpl_id"):
            template = template.browse(vals["product_tmpl_id"])
        if template and _is_variant_family(template):
            return False
        code = vals.get("engineering_code")
        if objBrowse is not None and "engineering_code" not in vals:
            code = objBrowse.engineering_code
        if not code or code == "-":
            return False
        return code


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends(
        "product_variant_ids.default_code",
        "product_variant_ids.active",
        "attribute_line_ids.attribute_id.create_variant",
    )
    def _compute_variant_default_code_error(self):
        """Warn only when a code is actually missing or will be missing.

        product_variant_default_code warns whenever the Reference Prefix is empty, also on
        templates whose variants all have a (manual) internal reference. Here the warning is
        shown when (a) an active variant has no internal reference, or (b) the template creates
        variants dynamically and not all of them exist yet, so new variants will be coded
        automatically. The text is computed per template (upstream reads value codes of all
        templates in the recordset).
        """
        automask = self.is_automask()
        for rec in self:
            rec.variant_default_code_error = rec._plm_variant_code_error(automask) or False

    def _plm_variant_code_error(self, automask):
        self.ensure_one()
        if not self.attribute_line_ids:
            return ""
        variants = self.product_variant_ids.filtered("active")
        missing = variants.filtered(lambda v: not v.default_code)
        if not missing and not self._plm_expects_new_variants(variants):
            return ""
        # same wording and layout as product_variant_default_code
        error = ""
        if not self.code_prefix and automask:
            error += self.env._("Reference Prefix is missing.") + "\n"
        empty_values = self.attribute_line_ids.value_ids.filtered(lambda v: not v.code)
        if empty_values:
            error += (self.env._("Following attribute value have an empty code :")
                      + "\n- " + "\n- ".join(empty_values.mapped("name")))
        if not error and missing:
            error = (self.env._("Variants without an internal reference:")
                     + "\n- " + "\n- ".join(missing.mapped("display_name")))
        if not error:
            return ""
        return self.env._("Default Code can not be computed.") + "\n" + error

    def _plm_expects_new_variants(self, variants):
        """Dynamic template whose possible combinations are not all created yet."""
        lines = self.attribute_line_ids.filtered(lambda line: line.attribute_id.create_variant != "no_variant")
        if not any(line.attribute_id.create_variant == "dynamic" for line in lines):
            return False
        return prod(len(line.value_ids) for line in lines) > len(variants)

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        templates._plm_family_codes_from_mask()
        return templates

    def write(self, vals):
        res = super().write(vals)
        if "attribute_line_ids" in vals or "engineering_code" in vals:
            self._plm_family_codes_from_mask()
        return res

    def _plm_family_codes_from_mask(self):
        """PLM variant families: odooplm's automatic code off (it gives every variant
        the same "CODE_REV"), so the variant mask is used."""
        families = self.filtered(
            lambda t: t.engineering_code and t.auto_default_code and _is_variant_family(t)
        )
        if families:
            families.write({"auto_default_code": False})

    def _plm_carry_over_from(self, old):
        # keep the code rule: prefix and (manual) mask of the previous revision
        self.write({"code_prefix": old.code_prefix})
        if old.reference_mask and old.reference_mask != self.reference_mask:
            self.write({"reference_mask": old.reference_mask})
        return super()._plm_carry_over_from(old)

    def _plm_variant_carry_over_vals(self, old_variant):
        vals = super()._plm_variant_carry_over_vals(old_variant)
        if not old_variant.manual_code:
            # generated from the mask: same rule, same code; copying would freeze it
            vals.pop("default_code", None)
        return vals
