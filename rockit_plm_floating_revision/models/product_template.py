# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, fields, models

_logger = logging.getLogger(__name__)
IN_USE_STATES = ("released", "undermodify", "obsoleted")
# template fields copied to a new revision when the copy left them empty
TEMPLATE_CARRY_OVER_FIELDS = (
    "image_1920", "engineering_material", "engineering_surface", "engineering_treatment",
    "std_description", "description_purchase", "description_sale",
)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    revision_effective_date = fields.Datetime(
        "Effective from",
        copy=False,
        help="Floating BoM lines use this revision from this moment on. Set on release "
        "when empty.",
    )
    revision_phase_out = fields.Selection(
        [("use_up", "Use up free stock first"), ("immediate", "Immediately")],
        "Phase-out when superseded",
        default="use_up",
        help="What floating BoM lines do with this revision once a newer revision is "
        "effective: consume its free stock first, or switch immediately.",
    )

    # ------------------------------------------------------------------ revisions
    def _plm_revisions(self):
        """Active templates sharing the engineering code, oldest revision first."""
        self.ensure_one()
        if not self.engineering_code:
            return self
        return self.search(
            [("engineering_code", "=", self.engineering_code)], order="engineering_revision asc"
        )

    def _plm_effective_revisions(self, at=None):
        """Return (current revision, superseded revisions to use up oldest first) at ``at``."""
        self.ensure_one()
        # a planned date in the past (an MO or RFQ not started yet) means "from now on"
        now = fields.Datetime.now()
        at = max(at, now) if at else now
        in_use = self._plm_revisions().filtered(lambda r: r.engineering_state in IN_USE_STATES)
        # effective = in use and its effective date reached (no date = effective); an
        # obsoleted revision stays current while its successor's date is in the future
        effective = in_use.filtered(
            lambda r: not r.revision_effective_date or r.revision_effective_date <= at
        )
        if not effective:
            return (in_use[:1] or self), self.browse()
        current = effective[-1]
        older = effective.filtered(
            lambda r: r.engineering_revision < current.engineering_revision
            and r.revision_phase_out == "use_up"
        )
        return current, older

    # ------------------------------------------------------------- access helpers
    def _plm_is_privileged_env(self):
        return self.env.su or self.env.uid == SUPERUSER_ID

    def _plm_can_revise(self):
        """PLM users who may create revisions (odooplm: Integration User and up)."""
        return self._plm_is_privileged_env() or self.env.user.has_group("plm.group_plm_integration_user")

    def _plm_can_release(self):
        """PLM users who may release revisions (odooplm: Release Users)."""
        return self._plm_is_privileged_env() or self.env.user.has_group("plm.group_plm_release_users")

    def _plm_transfer_env(self, model, allowed):
        """``model`` for the data a revision transfers (reordering rules, vendor prices,
        product images). PLM users are not inventory, purchase or website administrators:
        when ``allowed``, these records are read and written with sudo, limited to the
        records of this item's revisions in the companies of the current user (the
        company checks of the copied records still apply)."""
        Model = self.env[model]
        return Model.sudo() if allowed and not self.env.su else Model

    def _plm_company_domain(self):
        return [("company_id", "in", [False] + self.env.companies.ids)]

    # -------------------------------------------------- carry-over on new revision
    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        if self.env.context.get("rockit_plm_new_version"):
            # extra product images are rebuilt by _plm_carry_over_images (website_sale
            # lets only website editors create them, and the copy would lose their
            # attribute values anyway)
            for vals in vals_list:
                vals.pop("product_template_image_ids", None)
        return vals_list

    def new_version(self):
        res = super(ProductTemplate, self.with_context(rockit_plm_new_version=True)).new_version()
        for old in self:
            new = old.get_next_version()
            if new and new != old:
                new._plm_carry_over_from(old)
        return res

    def _plm_carry_over_from(self, old):
        """Copy the variant-level data odooplm leaves behind when it copies the template:
        variants (dynamic attributes create none), internal references, cost, vendor
        prices, routes, linked documents and bills of materials. Reordering rules move
        on release."""
        self.ensure_one()
        vals = {"route_ids": [(6, 0, old.route_ids.ids)]}
        # engineering and image data the template copy may leave empty
        for fname in TEMPLATE_CARRY_OVER_FIELDS:
            if fname in self._fields and old[fname] and not self[fname]:
                vals[fname] = old[fname]
        if "auto_default_code" in self._fields and old.product_variant_count > 1:
            # odooplm's automatic code would give every variant the same "CODE_REV"
            vals["auto_default_code"] = False
        self.write(vals)
        Supplier = self._plm_transfer_env("product.supplierinfo", self._plm_can_revise())
        company_domain = self._plm_company_domain()
        for old_variant in old.product_variant_ids:
            new_variant = old_variant._plm_counterpart(self, create=True)
            if not new_variant:
                _logger.warning("PLM carry-over: no variant on %s for %s",
                                self.display_name, old_variant.display_name)
                continue
            new_variant.write(self._plm_variant_carry_over_vals(old_variant))
            if "linkeddocuments" in new_variant._fields:
                new_variant.linkeddocuments = [(6, 0, old_variant.linkeddocuments.ids)]
            for seller in Supplier.search([("product_id", "=", old_variant.id)] + company_domain):
                seller.copy({"product_tmpl_id": self.id, "product_id": new_variant.id})
        for seller in Supplier.search([("product_tmpl_id", "=", old.id), ("product_id", "=", False)]
                                      + company_domain):
            seller.copy({"product_tmpl_id": self.id})
        self._plm_carry_over_images(old)
        self._plm_carry_over_boms(old)

    def _plm_carry_over_images(self, old):
        """Images: Odoo 20 (website_sale) keeps variant images as extra product images
        linked to attribute values. The template copy copies the images but not their
        attribute values, and dynamic variants are created empty: rebuild the extra images
        of the new revision from the old one (attribute values mapped to the new revision)
        and give each variant the main image of its counterpart."""
        ctx = {"skip_update_main_image": True, "from_extra_image": True}
        if "product_template_image_ids" in self._fields:
            Image = self._plm_transfer_env("product.image", self._plm_can_revise())
            new_ptavs = self.attribute_line_ids.product_template_value_ids
            old_images = Image.browse(old.product_template_image_ids.ids).sorted(lambda i: (i.sequence, i.id))
            new_images = Image.browse(self.product_template_image_ids.ids).sorted(lambda i: (i.sequence, i.id))
            if len(new_images) != len(old_images):
                # read the value now: creating the extra images may replace the attachment
                template_image = self.image_1920
                if hasattr(template_image, "to_base64"):
                    template_image = template_image.to_base64()
                new_images.with_context(**ctx).unlink()
                new_images = Image.browse([
                    image.with_context(**ctx).copy({"name": image.name, "product_tmpl_id": self.id}).id
                    for image in old_images])
                if template_image and not self.image_1920:
                    self.with_context(**ctx).image_1920 = template_image
            for old_image, new_image in zip(old_images, new_images):
                values = old_image.attribute_value_ids.product_attribute_value_id
                ptavs = new_ptavs.filtered(lambda v, values=values: v.product_attribute_value_id in values)
                if ptavs != new_image.attribute_value_ids or new_image.name != old_image.name:
                    new_image.with_context(**ctx).write(
                        {"name": old_image.name, "attribute_value_ids": [(6, 0, ptavs.ids)]})
            # stored compute that only depends on the image list
            self.product_variant_ids._compute_variant_image_ids()
        for old_variant in old.product_variant_ids.filtered("image_variant_1920"):
            new_variant = old_variant._plm_counterpart(self)
            if new_variant:
                new_variant.with_context(**ctx).image_variant_1920 = old_variant.image_variant_1920

    def _plm_carry_over_boms(self, old):
        """odooplm does not copy the bills of materials of a manufactured item to its
        new revision: copy them (variant-specific BoMs to the counterpart variant)."""
        Bom = self.env["mrp.bom"]
        if Bom.search_count([("product_tmpl_id", "=", self.id)]):
            return Bom
        new_boms = Bom
        for bom in Bom.search([("product_tmpl_id", "=", old.id)]):
            vals = {"product_tmpl_id": self.id}
            if bom.product_id:
                vals["product_id"] = bom.product_id._plm_counterpart(self, create=True).id
            new_boms |= bom.copy(vals)
        return new_boms

    def _plm_variant_carry_over_vals(self, old_variant):
        """Values copied from a variant of the previous revision to its counterpart."""
        vals = {
            "default_code": old_variant.default_code,
            "standard_price": old_variant.standard_price,
            "volume": old_variant.volume,
            "barcode": False,
        }
        # weight: plm_automatic_weight computes it from these when installed
        for fname in ("automatic_compute_selection", "weight_additional", "weight_cad", "weight"):
            if fname in old_variant._fields:
                vals[fname] = old_variant[fname]
        return vals

    # ---------------------------------------------------- replenishment on release
    def write(self, vals):
        res = super().write(vals)
        if vals.get("engineering_state") == "released":
            for template in self:
                template._plm_on_release()
        if {"engineering_state", "revision_effective_date", "revision_phase_out"} & set(vals):
            self.product_variant_ids._plm_update_family_orderpoints()
        return res

    def _plm_on_release(self):
        """Set the effective date and move reordering rules from older revisions."""
        self.ensure_one()
        if not self.revision_effective_date:
            self.revision_effective_date = fields.Datetime.now()
        # release users need not be inventory administrators to move the rules
        Orderpoint = self._plm_transfer_env("stock.warehouse.orderpoint", self._plm_can_release())
        older = self._plm_revisions().filtered(
            lambda r: r.engineering_revision < self.engineering_revision
        )
        for orderpoint in Orderpoint.search([("product_id", "in", older.product_variant_ids.ids)]
                                            + self._plm_company_domain()):
            new_variant = orderpoint.product_id._plm_counterpart(self, create=True)
            if new_variant and not Orderpoint.search_count([
                ("product_id", "=", new_variant.id),
                ("location_id", "=", orderpoint.location_id.id),
            ]):
                orderpoint.copy({"product_id": new_variant.id})
            orderpoint.active = False
        self._plm_notify_release_impact()

    # ------------------------------------------------- open orders on old revisions
    def _plm_release_impact(self):
        """Open documents that still use an older revision of this item.

        :return: list of plm.release.impact.line values: unstarted manufacturing order
            components (the part not covered by old stock that is used up first is
            proposed to move to the revision effective at the MO start), RFQ lines (to
            the revision effective at the planned date) and confirmed purchase lines
            (listed only: agree changes with the vendor)
        """
        self.ensure_one()
        older = self._plm_revisions().filtered(
            lambda r: r.engineering_revision < self.engineering_revision
        )
        old_variants = older.with_context(active_test=False).product_variant_ids
        if not old_variants:
            return []
        lines = []
        moves = self.env["stock.move"].search([
            ("raw_material_production_id.state", "in", ("draft", "confirmed")),
            ("product_id", "in", old_variants.ids),
            ("state", "not in", ("done", "cancel")),
        ]).sorted(lambda m: (m.raw_material_production_id.date_start, m.id))
        available = {}
        for move in moves:
            key = (move.product_id, move.raw_material_production_id.location_src_id)
            if key not in available:
                same = moves.filtered(lambda m, key=key: (m.product_id, m.raw_material_production_id.location_src_id) == key)
                free = key[0].with_context(location=key[1].id).free_qty
                available[key] = max(free, 0.0) + sum(same.mapped("quantity"))
        for move in moves:
            production = move.raw_material_production_id
            product = move.product_id
            key = (product, production.location_src_id)
            current, use_up = product.product_tmpl_id._plm_effective_revisions(production.date_start)
            vals = {
                "kind": "mo", "document": production.name, "date": production.date_start,
                "move_id": move.id, "product_id": product.id, "quantity": move.product_uom_qty,
            }
            if product.product_tmpl_id == current or current.engineering_revision < product.engineering_revision:
                lines.append(dict(vals, keep_qty=move.product_uom_qty, can_update=False,
                                  note=self.env._("Newer revision not effective at the MO start")))
                continue
            keep = 0.0
            if product.product_tmpl_id in use_up:
                keep = min(move.product_uom_qty, available[key])
                available[key] -= keep
            new_product = product._plm_counterpart(current, create=True)
            switch = move.product_uom_qty - keep
            if move.uom_id.compare(switch, 0.0) <= 0:
                lines.append(dict(vals, keep_qty=keep, new_product_id=new_product.id, can_update=False,
                                  note=self.env._("Covered by old revision stock (used up first)")))
                continue
            lines.append(dict(vals, keep_qty=keep, new_product_id=new_product.id, can_update=True,
                              update=True, note=self.env._(
                                  "%(qty)s to revision %(rev)s", qty=switch, rev=current.engineering_revision)))
        productions = self.env["mrp.production"].search([
            ("product_id", "in", old_variants.ids),
            ("state", "in", ("draft", "confirmed")),
        ])
        for production in productions:
            current = production.product_id.product_tmpl_id._plm_effective_revisions(production.date_start)[0]
            vals = {
                "kind": "mo_product", "document": production.name, "date": production.date_start,
                "production_id": production.id, "product_id": production.product_id.id,
                "quantity": production.product_qty,
            }
            if current == production.product_id.product_tmpl_id or current.engineering_revision < production.product_id.engineering_revision:
                lines.append(dict(vals, can_update=False,
                                  note=self.env._("Newer revision not effective at the MO start")))
                continue
            new_product = production.product_id._plm_counterpart(current, create=True)
            if production.state == "draft":
                lines.append(dict(vals, new_product_id=new_product.id, can_update=True, update=True,
                                  note=self.env._("Produce revision %(rev)s (draft MO: product and BoM updated)",
                                                  rev=current.engineering_revision)))
            else:
                lines.append(dict(vals, new_product_id=new_product.id, can_update=False,
                                  note=self.env._("Confirmed MO produces the old revision: cancel and re-plan if needed")))
        purchase_lines = self.env["purchase.order.line"].search([
            ("product_id", "in", old_variants.ids),
            ("order_id.state", "in", ("draft", "sent", "to approve", "purchase")),
        ])
        for line in purchase_lines:
            vals = {
                "document": line.order_id.name, "date": line.date_planned,
                "purchase_line_id": line.id, "product_id": line.product_id.id,
                "quantity": line.product_qty,
            }
            if line.order_id.state == "purchase":
                if line.uom_id.compare(line.qty_received, line.product_qty) >= 0:
                    continue
                current = line.product_id.product_tmpl_id._plm_effective_revisions(line.date_planned)[0]
                lines.append(dict(vals, kind="po", can_update=False,
                                  new_product_id=line.product_id._plm_counterpart(current).id,
                                  note=self.env._("Confirmed: agree a change with the vendor")))
                continue
            current = line.product_id.product_tmpl_id._plm_effective_revisions(line.date_planned)[0]
            if current == line.product_id.product_tmpl_id or current.engineering_revision < line.product_id.engineering_revision:
                lines.append(dict(vals, kind="rfq", can_update=False,
                                  note=self.env._("Newer revision not effective at the planned date")))
                continue
            lines.append(dict(vals, kind="rfq", can_update=True, update=True,
                              new_product_id=line.product_id._plm_counterpart(current, create=True).id,
                              note=self.env._("Buy revision %(rev)s instead", rev=current.engineering_revision)))
        return lines

    def _plm_notify_release_impact(self):
        lines = self._plm_release_impact()
        if not lines:
            return
        counts = {kind: len([v for v in lines if v["kind"] == kind]) for kind in ("mo", "rfq", "po")}
        self.message_post(body=self.env._(
            "Revision %(rev)s released. Open orders still on older revisions: %(mo)s "
            "manufacturing order component(s), %(rfq)s RFQ line(s), %(po)s confirmed "
            "purchase line(s). Review them with \"Open orders\" on the product.",
            rev=self.engineering_revision, mo=counts["mo"], rfq=counts["rfq"], po=counts["po"],
        ))

    def action_plm_release_impact(self):
        self.ensure_one()
        return self.env["plm.release.impact"]._plm_open_for(self)
