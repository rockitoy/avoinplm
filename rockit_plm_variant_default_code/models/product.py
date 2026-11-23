# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
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
