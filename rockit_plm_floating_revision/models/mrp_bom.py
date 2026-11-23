# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.api import NewId

DATE_CTX = "plm_floating_date"
LOCATION_CTX = "plm_floating_location"
NO_FLOAT_CTX = "plm_floating_disable"
SPLIT_REF = "plm_split_"
# set by rockit_bom_attribute_match_dynamic while exploding: missing variants may be created
CREATE_CTX = "bom_attribute_match_create_variant"


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    float_revision = fields.Boolean(
        "Floating revision",
        default=True,
        help="Use the revision of this PLM item that is effective at use time (and use "
        "up superseded revisions first) instead of exactly the revision on the line.",
    )
    component_revision = fields.Char(
        "Revision",
        compute="_compute_component_revision",
        help="Revision on the line; '↻' = floating, the number is the revision "
        "effective now.",
    )

    @api.depends("product_id", "float_revision")
    def _compute_component_revision(self):
        for line in self:
            template = line._plm_component_template()
            if not template.engineering_code:
                line.component_revision = False
            elif line.float_revision:
                line.component_revision = line._plm_floating_revision_label(template)
            else:
                line.component_revision = str(template.engineering_revision)

    def _plm_component_template(self):
        """PLM item (template) of the line. Extended by the component family bridge."""
        self.ensure_one()
        return self.product_id.product_tmpl_id

    def _plm_floating_revision_label(self, template):
        current = template._plm_effective_revisions()[0]
        return f"↻ {current.engineering_revision}"

    def _plm_virtual_copy(self, product, index=0):
        """In-memory copy of the line for another revision of its component. Not linked
        with ``origin`` (two new records with the same origin are the same record); the
        real line is encoded in ``ref`` and restored by ``_plm_real_line``."""
        self.ensure_one()
        return self.new({
            "bom_id": self.bom_id.id,
            "product_id": product.id,
            "product_qty": self.product_qty,
            "uom_id": self.uom_id.id,
            "operation_id": self.operation_id.id,
            "sequence": self.sequence,
        }, ref=f"{SPLIT_REF}{self.id}_{index}")

    def _plm_real_line(self):
        self.ensure_one()
        ref = isinstance(self.id, NewId) and self.id.ref
        if ref and str(ref).startswith(SPLIT_REF):
            return self.browse(int(str(ref)[len(SPLIT_REF):].split("_")[0]))
        return self._origin

    def _plm_floats(self):
        self.ensure_one()
        return bool(self.float_revision and self.product_id.engineering_code)

    def _plm_fixed_floating(self):
        """Floating line with a fixed component (resolved here, not by attribute match)."""
        self.ensure_one()
        return self._plm_floats()


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def _plm_resolve_one(self, bom_line, product):
        """Revision for one unit of the line (BoM cost, structure report)."""
        if not product or not bom_line.float_revision or not product.engineering_code:
            return product
        allocation = product._plm_allocate(
            bom_line.product_qty,
            at=self.env.context.get(DATE_CTX),
            location=self.env.context.get(LOCATION_CTX),
            create=bool(self.env.context.get(CREATE_CTX)),
        )
        return allocation[0][0]

    def _plm_resolved_by_attribute_match(self):
        """True when another module (the component family bridge) virtualises this BoM
        and resolves its floating lines; the hooks below then leave it alone."""
        return False

    def _plm_prepare_floating_bom(self, bom, product):
        """In-memory copy of ``bom`` whose fixed floating lines use the revision effective
        for ``product`` (BoM cost, structure report)."""
        if self.env.context.get(NO_FLOAT_CTX) or not product or product._name != "product.product":
            return bom
        fixed = bom.bom_line_ids.filtered(lambda l: l._plm_fixed_floating())
        if not fixed:
            return bom
        if isinstance(bom.id, int):
            bom = bom.new(origin=bom)
            fixed = bom.bom_line_ids.filtered(lambda l: l._plm_fixed_floating())
        for line in fixed:
            line.product_id = self._plm_resolve_one(line, line.product_id)
        return bom

    def _plm_has_floating_lines(self):
        return any(l._plm_fixed_floating() for l in self.bom_line_ids)

    # MOs and procurement: full quantity, split over revisions
    def explode(self, product, quantity, picking_type=False, never_attribute_values=False):
        boms_done, lines_done = super().explode(
            product, quantity, picking_type=picking_type, never_attribute_values=never_attribute_values
        )
        if self.env.context.get(NO_FLOAT_CTX):
            return boms_done, lines_done
        at = self.env.context.get(DATE_CTX)
        location = self.env.context.get(LOCATION_CTX)
        result = []
        for line, data in lines_done:
            component = line.product_id
            if not component or not line.float_revision or not component.engineering_code:
                result.append((line, data))
                continue
            qty = line.uom_id._compute_quantity(data["qty"], component.uom_id, round=False)
            allocation = component.with_context(**{NO_FLOAT_CTX: True})._plm_allocate(
                qty, at=at, location=location, create=True
            )
            if len(allocation) == 1 and allocation[0][0] == component:
                result.append((line, data))
                continue
            for index, (variant, variant_qty) in enumerate(allocation):
                line_qty = variant.uom_id._compute_quantity(variant_qty, line.uom_id, round=False)
                result.append((line._plm_virtual_copy(variant, index), dict(data, qty=line_qty)))
        return boms_done, result
