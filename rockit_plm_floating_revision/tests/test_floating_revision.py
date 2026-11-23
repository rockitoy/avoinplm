# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io

from odoo.tests import TransactionCase, tagged


def _png(color):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _content(value):
    return getattr(value, "content", value)


class FloatingRevisionCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls.warehouse = cls.env["stock.warehouse"].search([("lot_stock_id", "=", cls.stock.id)], limit=1)
        cls.other_location = cls.env["stock.location"].create({"name": "FR quarantine", "usage": "internal"})
        cls.vendor = cls.env["res.partner"].create({"name": "FR vendor"})
        Attr = cls.env["product.attribute"]
        cls.size = Attr.create({"name": "FR Size", "create_variant": "dynamic",
                                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "M"})]})
        PT = cls.env["product.template"]
        cls.buy = cls.env["stock.route"].create({"name": "FR route", "product_selectable": True})
        # PLM family with size variants (dynamic attribute: odooplm copies no variant)
        cls.frame = PT.create({
            "name": "FR Frame", "type": "consu", "is_storable": True, "engineering_code": "FR-FRAME",
            "auto_default_code": False, "route_ids": [(6, 0, cls.buy.ids)],
            "attribute_line_ids": [(0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})],
        })
        for ptav in cls.frame.attribute_line_ids.product_template_value_ids:
            variant = cls.frame._create_product_variant(ptav)
            variant.write({"default_code": "FR-FRAME-" + ptav.name, "standard_price": 100})
            cls.env["product.supplierinfo"].create({"partner_id": cls.vendor.id, "product_tmpl_id": cls.frame.id,
                                                    "product_id": variant.id, "price": 90, "delay": 21})
            cls.env["stock.warehouse.orderpoint"].create({"product_id": variant.id, "location_id": cls.stock.id,
                                                          "product_min_qty": 1, "product_max_qty": 4})
        cls.frame_m = cls.frame.product_variant_ids.filtered(lambda p: p.default_code == "FR-FRAME-M")
        cls.doc = cls.env["ir.attachment"].create({"name": "FR drawing.pdf", "raw": b"%PDF-1.4",
                                                   "engineering_code": "FR-DOC", "engineering_state": "released", "is_plm": True})
        cls.frame_m.linkeddocuments = [(4, cls.doc.id)]
        # PLM single item (fixed BoM line)
        cls.fork = PT.create({"name": "FR Fork", "type": "consu", "is_storable": True,
                              "engineering_code": "FR-FORK", "auto_default_code": False, "default_code": "FR-FORK"})
        (cls.frame | cls.fork).write({"engineering_state": "released"})
        # assembly with the size attribute: frame line (see _frame_line_vals) + fixed line (fork)
        cls.assembly = PT.create({"name": "FR Bike", "type": "consu", "attribute_line_ids": [
            (0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})]})
        cls.bike_m = cls.assembly._create_product_variant(
            cls.assembly.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "M"))
        cls.bom = cls.env["mrp.bom"].create({"product_tmpl_id": cls.assembly.id, "bom_line_ids": [
            (0, 0, cls._frame_line_vals()),
            (0, 0, {"product_id": cls.fork.product_variant_id.id, "product_qty": 1})]})

    @classmethod
    def _frame_line_vals(cls):
        """BoM line of the frame for the M bike. Fixed line here; the component family
        bridge runs the same tests with an attribute-matched (template) line."""
        return {"product_id": cls.frame_m.id, "product_qty": 1}

    # helpers
    def _new_revision(self, template, revise_docs=False):
        variant = template.product_variant_ids[:1]
        wizard = self.env["product.rev_wizard"].with_context(
            active_id=variant.id, active_model="product.product").create({"reviseDocument": revise_docs})
        wizard.action_create_new_revision_by_server()
        return template.get_next_version()

    def _release(self, template):
        variant = template.product_variant_ids[:1]
        variant.action_confirm()
        variant.action_release()

    def _stock(self, product, qty, location=None):
        self.env["stock.quant"]._update_available_quantity(product, location or self.stock, qty)
        self.env.invalidate_all()

    def _mo(self, qty):
        mo = self.env["mrp.production"].create({"product_id": self.bike_m.id, "bom_id": self.bom.id, "product_qty": qty})
        mo.action_confirm()
        return mo

    def _fork_line(self):
        return self.bom.bom_line_ids.filtered(lambda l: l.product_id == self.fork.product_variant_id)

    def _moves(self, mo, code):
        moves = mo.move_raw_ids.filtered(lambda m: m.product_id.engineering_code == code)
        return sorted((m.product_id.engineering_revision, m.product_uom_qty) for m in moves)


@tagged("post_install", "-at_install")
class TestFloatingRevision(FloatingRevisionCommon):
    def test_carry_over(self):
        rev1 = self._new_revision(self.frame, revise_docs=True)
        self.assertEqual(rev1.engineering_revision, 1)
        self.assertEqual(sorted(rev1.product_variant_ids.mapped("default_code")), ["FR-FRAME-M", "FR-FRAME-S"])
        self.assertEqual(rev1.route_ids, self.buy)
        new_m = self.frame_m._plm_counterpart(rev1)
        self.assertEqual(len(rev1.seller_ids.filtered(lambda s: s.product_id == new_m)), 1)
        self.assertEqual(new_m.standard_price, 100)
        self.assertEqual(new_m.linkeddocuments.engineering_code, "FR-DOC")
        self.assertEqual(new_m.linkeddocuments.engineering_revision, 1, "document revised with the item")
        self.assertEqual(new_m.plm_revision, "1")
        self.assertFalse(self.fork.product_variant_id.linkeddocuments)

    def test_carry_over_images_and_engineering_fields(self):
        size_s = self.frame.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "S")
        self.frame.write({"image_1920": _png("red"), "engineering_material": "FR aluminium",
                          "engineering_surface": "FR raw", "engineering_treatment": "FR none"})
        weight = {"weight_additional": 1.8} if "weight_additional" in self.frame_m._fields else {"weight": 1.8}
        self.frame_m.write(dict(weight, image_variant_1920=_png("blue"), volume=0.05))
        has_images = "product_template_image_ids" in self.frame._fields
        if has_images:
            self.env["product.image"].create({"name": "FR S picture", "image_1920": _png("green"),
                                              "product_tmpl_id": self.frame.id,
                                              "attribute_value_ids": [(6, 0, size_s.ids)]})
        rev1 = self._new_revision(self.frame)
        self.assertEqual(rev1.engineering_material, "FR aluminium")
        self.assertEqual(rev1.engineering_surface, "FR raw")
        self.assertEqual(rev1.engineering_treatment, "FR none")
        self.assertEqual(_content(rev1.image_1920), _content(self.frame.image_1920))
        new_m = self.frame_m._plm_counterpart(rev1)
        self.assertEqual(_content(new_m.image_variant_1920), _content(self.frame_m.image_variant_1920),
                         "variant image carried over")
        self.assertEqual((new_m.weight, new_m.volume), (self.frame_m.weight, 0.05))
        if "weight_additional" in new_m._fields:
            self.assertEqual(new_m.weight_additional, self.frame_m.weight_additional)
        self.assertEqual(new_m.engineering_material, "FR aluminium")
        if has_images:
            old_images = self.frame.product_template_image_ids
            images = rev1.product_template_image_ids
            self.assertEqual(len(images), len(old_images), "no duplicate images: %s / %s" % (
                [(i.name, i.type, i.attribute_value_ids.mapped("name")) for i in images],
                [(i.name, i.type, i.attribute_value_ids.mapped("name")) for i in old_images]))
            self.assertEqual(images.attribute_value_ids.product_tmpl_id, rev1, "mapped to the new revision")
            self.assertEqual(sorted(images.attribute_value_ids.mapped("name")),
                             sorted(old_images.attribute_value_ids.mapped("name")))
            image = images.filtered(lambda i: i.name == "FR S picture")
            new_s = self.frame.product_variant_ids.filtered(lambda p: p.default_code == "FR-FRAME-S")._plm_counterpart(rev1)
            self.assertIn(image, new_s.variant_image_ids)
        # a further revision keeps them too
        self._release(rev1)
        rev2 = self._new_revision(rev1)
        self.assertEqual(rev2.engineering_material, "FR aluminium")
        self.assertEqual(_content(self.frame_m._plm_counterpart(rev2).image_variant_1920),
                         _content(self.frame_m.image_variant_1920))

    def test_release_moves_orderpoints(self):
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        self.assertEqual(self.frame.engineering_state, "obsoleted")
        self.assertTrue(rev1.revision_effective_date)
        OP = self.env["stock.warehouse.orderpoint"]
        self.assertFalse(OP.search([("product_id", "in", self.frame.product_variant_ids.ids)]))
        self.assertEqual(len(OP.search([("product_id", "in", rev1.product_variant_ids.ids)])), 2)

    def test_draft_revision_not_used(self):
        self._new_revision(self.frame)
        mo = self._mo(1)
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 1)])

    def test_use_up_split_full_quantity(self):
        self._stock(self.frame_m, 2)
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        mo = self._mo(5)
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 2), (1, 3)])
        self.assertTrue(all(m.bom_line_id.bom_id == self.bom for m in mo.move_raw_ids))
        # rev 0 now reserved -> next MO only rev 1
        self.assertEqual(self._moves(self._mo(1), "FR-FRAME"), [(1, 1)])

    def test_location_aware(self):
        self._stock(self.frame_m, 3, self.other_location)  # not under the MO source location
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        self.assertEqual(self._moves(self._mo(1), "FR-FRAME"), [(1, 1)])

    def test_immediate_phase_out(self):
        self._stock(self.frame_m, 2)
        self.frame.revision_phase_out = "immediate"
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        self.assertEqual(self._moves(self._mo(1), "FR-FRAME"), [(1, 1)])

    def test_fixed_line_floats(self):
        fork_rev1 = self._new_revision(self.fork)
        self.assertEqual(self._fork_line().component_revision, "↻ 0")
        self._release(fork_rev1)
        mo = self._mo(1)
        self.assertEqual(self._moves(mo, "FR-FORK"), [(1, 1)])
        self.env.invalidate_all()
        self.assertEqual(self._fork_line().component_revision, "↻ 1")
        # BoM line itself unchanged
        self.assertEqual(self._fork_line().product_id.engineering_revision, 0)
        # fixed (non-floating) line keeps its exact revision
        self._fork_line().float_revision = False
        self.assertEqual(self._moves(self._mo(1), "FR-FORK"), [(0, 1)])

    def test_effective_date_in_future(self):
        rev1 = self._new_revision(self.frame)
        rev1.revision_effective_date = "2999-01-01 00:00:00"
        self._release(rev1)
        self.assertEqual(self._moves(self._mo(1), "FR-FRAME"), [(0, 1)])

    def test_cost_and_report_use_effective_revision(self):
        fork_rev1 = self._new_revision(self.fork)
        self._release(fork_rev1)
        fork_rev1.product_variant_id.standard_price = 40
        self.fork.product_variant_id.standard_price = 10
        data = self.env["report.mrp.report_bom_structure"]._get_report_data(self.bom.id, searchVariant=self.bike_m.id)
        revs = {c["name"]: c.get("plm_revision") for c in data["lines"]["components"]}
        self.assertIn("1", [r for n, r in revs.items() if "FR Fork" in n])
        self.bike_m.button_bom_cost()
        self.assertGreaterEqual(self.bike_m.standard_price, 140)  # frame 100 + fork rev1 40

    def test_revision_columns(self):
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        mo = self._mo(1)
        move = mo.move_raw_ids.filtered(lambda m: m.product_id.engineering_code == "FR-FRAME")
        self.assertEqual(move.product_revision, "1")
        self.assertEqual(mo.product_revision, False)
        po_line = self.env["purchase.order.line"].new({"product_id": move.product_id.id})
        self.assertEqual(po_line.product_revision, "1")

    # milestone 2: phase-in replenishment and release impact
    def _orderpoint(self, variant):
        orderpoint = self.env["stock.warehouse.orderpoint"].search([("product_id", "=", variant.id)])
        self.env.invalidate_all()
        return orderpoint

    def test_phase_in_replenishment(self):
        # rule min 1 / max 4; S has 3 old pieces, M none
        frame_s = self.frame.product_variant_ids - self.frame_m
        self._stock(frame_s, 3)
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        new_s, new_m = frame_s._plm_counterpart(rev1), self.frame_m._plm_counterpart(rev1)
        op_s, op_m = self._orderpoint(new_s), self._orderpoint(new_m)
        self.assertEqual(op_s.plm_phase_in_qty, 3)
        self.assertEqual(op_s.qty_forecast, 3)
        self.assertEqual(op_s.qty_to_order, 0, "old S stock covers the minimum: nothing to buy")
        self.assertEqual(op_m.qty_to_order, 4)
        # demand that consumes the old stock (allocated to rev 0) brings rev 1 back to ordering
        bike_s = self.assembly._create_product_variant(
            self.assembly.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "S"))
        bom_s = self.env["mrp.bom"].create({
            "product_tmpl_id": self.assembly.id, "product_id": bike_s.id,
            "bom_line_ids": [(0, 0, {"product_id": frame_s.id, "product_qty": 1})]})
        mo = self.env["mrp.production"].create({"product_id": bike_s.id, "bom_id": bom_s.id, "product_qty": 3})
        mo.action_confirm()
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 3)])
        op_s = self._orderpoint(new_s)
        self.assertEqual(op_s.plm_phase_in_qty, 0)
        self.assertEqual(op_s.qty_to_order, 4)
        # immediate phase-out: old stock is not counted
        self.frame.revision_phase_out = "immediate"
        self._stock(frame_s, 2)
        self.assertEqual(self._orderpoint(new_s).plm_phase_in_qty, 0)

    def test_release_impact(self):
        self._stock(self.frame_m, 1)
        mo = self._mo(3)  # 3 x rev 0 (only 1 in stock)
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 3)])
        rfq = self.env["purchase.order"].create({"partner_id": self.vendor.id, "order_line": [
            (0, 0, {"product_id": self.frame_m.id, "product_qty": 5})]})
        po = self.env["purchase.order"].create({"partner_id": self.vendor.id, "order_line": [
            (0, 0, {"product_id": self.frame_m.id, "product_qty": 2})]})
        po.button_confirm()
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        self.assertIn("Open orders", rev1.message_ids[:1].body)
        action = rev1.action_plm_release_impact()
        wizard = self.env["plm.release.impact"].browse(action["res_id"])
        # (the MO may also have created an RFQ from the reordering rule: same handling)
        by_doc = {line.document: line for line in wizard.line_ids}
        mo_line, rfq_line, po_line = by_doc[mo.name], by_doc[rfq.name], by_doc[po.name]
        self.assertEqual((mo_line.kind, rfq_line.kind, po_line.kind), ("mo", "rfq", "po"))
        self.assertEqual((mo_line.keep_qty, mo_line.quantity), (1, 3), "1 old piece used up, 2 move")
        self.assertTrue(mo_line.can_update and rfq_line.can_update)
        self.assertFalse(po_line.can_update)
        new_m = self.frame_m._plm_counterpart(rev1)
        new_m.variant_seller_ids.filtered(lambda s: s.product_id == new_m).price = 123.0
        wizard.line_ids.write({"update": True})
        wizard.action_apply()
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 1), (1, 2)])
        self.assertEqual(rfq.order_line.product_id, new_m)
        self.assertEqual(rfq.order_line.product_qty, 5)
        self.assertEqual(rfq.order_line.price_unit, 123.0, "vendor price of the new revision")
        self.assertEqual(po.order_line.product_id, self.frame_m, "confirmed PO untouched")
        # second run: nothing left to update for the MO and RFQ
        wizard = self.env["plm.release.impact"].browse(rev1.action_plm_release_impact()["res_id"])
        self.assertFalse(wizard.line_ids.filtered("can_update"))

    def test_release_impact_future_effectivity(self):
        mo = self._mo(1)
        rev1 = self._new_revision(self.frame)
        rev1.revision_effective_date = "2099-01-01 00:00:00"
        self._release(rev1)
        wizard = self.env["plm.release.impact"].browse(rev1.action_plm_release_impact()["res_id"])
        self.assertEqual(wizard.line_ids.filtered(lambda line: line.kind == "mo").move_id.raw_material_production_id, mo)
        self.assertFalse(wizard.line_ids.filtered("can_update"), "nothing to move before the effective date")
        self.assertEqual(self._moves(mo, "FR-FRAME"), [(0, 1)])

    # milestone 3: manufactured PLM items and manual reordering rules
    def _wheel(self):
        wheel = self.env["product.template"].create({
            "name": "FR Wheel", "type": "consu", "is_storable": True, "engineering_code": "FR-WHEEL",
            "auto_default_code": False})
        self.env["mrp.bom"].create({"product_tmpl_id": wheel.id, "bom_line_ids": [
            (0, 0, {"product_id": self.fork.product_variant_id.id, "product_qty": 2})]})
        wheel.engineering_state = "released"
        return wheel

    def test_bom_carried_over(self):
        wheel = self._wheel()
        rev1 = self._new_revision(wheel)
        bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", rev1.id)])
        self.assertEqual(len(bom), 1)
        self.assertEqual(bom.bom_line_ids.product_qty, 2)

    def test_release_impact_mo_producing_old_revision(self):
        wheel = self._wheel()
        draft_mo = self.env["mrp.production"].create({"product_id": wheel.product_variant_id.id, "product_qty": 1})
        confirmed_mo = self.env["mrp.production"].create({"product_id": wheel.product_variant_id.id, "product_qty": 1})
        confirmed_mo.action_confirm()
        rev1 = self._new_revision(wheel)
        self._release(rev1)
        wizard = self.env["plm.release.impact"].browse(rev1.action_plm_release_impact()["res_id"])
        lines = {line.document: line for line in wizard.line_ids.filtered(lambda l: l.kind == "mo_product")}
        self.assertTrue(lines[draft_mo.name].can_update)
        self.assertFalse(lines[confirmed_mo.name].can_update)
        wizard.action_apply()
        self.assertEqual(draft_mo.product_id.product_tmpl_id, rev1)
        self.assertEqual(draft_mo.bom_id.product_tmpl_id, rev1)
        self.assertEqual(confirmed_mo.product_id.product_tmpl_id, wheel)

    def test_manual_orderpoint_merged_and_shortage_passed_on(self):
        rev1 = self._new_revision(self.frame)
        self._release(rev1)
        new_m = self.frame_m._plm_counterpart(rev1)
        # demand still on rev 0 without stock (e.g. an MO confirmed before the release)
        self.env["stock.move"].create({
            "product_id": self.frame_m.id, "product_uom_qty": 3, "location_id": self.stock.id,
            "location_dest_id": self.env.ref("stock.stock_location_customers").id}).with_context(
            plm_floating_disable=True)._action_confirm()
        OP = self.env["stock.warehouse.orderpoint"].with_context(active_test=False)
        manual = OP.create({"product_id": self.frame_m.id, "location_id": self.other_location.id,
                            "trigger": "manual", "product_min_qty": 0, "product_max_qty": 0})
        OP._plm_merge_superseded_manual_orderpoints()
        self.assertFalse(manual.exists())
        self.assertTrue(OP.search([("product_id", "=", new_m.id), ("location_id", "=", self.other_location.id)]))
        op_m = self._orderpoint(new_m).filtered(lambda o: o.location_id == self.stock)
        self.assertEqual(op_m.plm_phase_in_qty, -3, "old revision shortage counted")
        self.assertEqual(op_m.qty_to_order, 7, "max 4 + 3 old shortage")
