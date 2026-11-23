# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPlmEco(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock = cls.env.ref("stock.stock_location_stock")
        Attr = cls.env["product.attribute"]
        cls.size = Attr.create({"name": "ECO Size", "create_variant": "dynamic",
                                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "M"})]})
        PT = cls.env["product.template"]
        cls.frame = PT.create({
            "name": "ECO Frame", "type": "consu", "is_storable": True, "engineering_code": "ECO-FRAME",
            "auto_default_code": False,
            "attribute_line_ids": [(0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})],
        })
        for ptav in cls.frame.attribute_line_ids.product_template_value_ids:
            cls.frame._create_product_variant(ptav).default_code = "ECO-FRAME-" + ptav.name
        cls.frame_m = cls.frame.product_variant_ids.filtered(lambda p: p.default_code == "ECO-FRAME-M")
        cls.frame.engineering_state = "released"
        cls.bike = PT.create({"name": "ECO Bike", "type": "consu", "sale_ok": True, "attribute_line_ids": [
            (0, 0, {"attribute_id": cls.size.id, "value_ids": [(6, 0, cls.size.value_ids.ids)]})]})
        cls.bike_m = cls.bike._create_product_variant(
            cls.bike.attribute_line_ids.product_template_value_ids.filtered(lambda v: v.name == "M"))
        cls.bolt = cls.env["product.product"].create({"name": "ECO Bolt", "type": "consu"})
        cls.bom = cls.env["mrp.bom"].create({"product_tmpl_id": cls.bike.id, "bom_line_ids": [
            (0, 0, cls._frame_line_vals())]})
        cls.request_type = cls.env["mail.activity.type"].search([("change_activity_type", "=", "request")], limit=1)

    @classmethod
    def _frame_line_vals(cls):
        # attribute-matched line when the configurator modules are installed, else fixed
        if "component_template_id" in cls.env["mrp.bom.line"]._fields:
            return {"component_template_id": cls.frame.id, "product_qty": 1}
        return {"product_id": cls.frame_m.id, "product_qty": 1}

    def _stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(product, self.stock, qty)
        self.env.invalidate_all()

    def _eco(self, **vals):
        return self.env["plm.eco"].create(dict({
            "title": "Wider tyre clearance", "line_ids": [(0, 0, {"product_tmpl_id": self.frame.id})]}, **vals))

    def _release(self, template):
        variant = template.product_variant_ids[:1]
        variant.action_confirm()
        variant.action_release()

    def _mo(self, qty=1):
        mo = self.env["mrp.production"].create({"product_id": self.bike_m.id, "bom_id": self.bom.id, "product_qty": qty})
        mo.action_confirm()
        moves = mo.move_raw_ids.filtered(lambda m: m.product_id.engineering_code == "ECO-FRAME")
        return sorted((m.product_id.engineering_revision, m.product_uom_qty) for m in moves)

    def test_ecr_becomes_eco(self):
        self.assertTrue(self.request_type, "odooplm change request activity type")
        ecr = self.env["mail.activity"].create({
            "activity_type_id": self.request_type.id, "summary": "ECR-T1 Wider tyre clearance",
            "res_model_id": self.env["ir.model"]._get_id("product.product"), "res_id": self.frame_m.id,
            "user_id": self.env.user.id, "plm_state": "in_progress"})
        ecr.action_to_eco()
        self.assertEqual(ecr.plm_state, "eco")
        eco = ecr.plm_eco_ids
        self.assertEqual(len(eco), 1)
        self.assertTrue(eco.name.startswith("ECO-"))
        self.assertEqual(eco.line_ids.product_tmpl_id, self.frame)
        self.assertEqual(eco.ecr_reference, "ECR-T1 Wider tyre clearance")
        # the ECO closes the ECR when its revision is released
        eco.action_start()
        self._release(eco.line_ids.new_tmpl_id)
        self.assertEqual(eco.state, "done")
        self.assertEqual(ecr.with_context(active_test=False).plm_state, "done")

    def test_impact_analysis(self):
        self._stock(self.frame_m, 2)
        mo = self.env["mrp.production"].create({"product_id": self.bike_m.id, "bom_id": self.bom.id, "product_qty": 1})
        eco = self._eco()
        eco.action_analyze()
        kinds = {(i.kind, i.document) for i in eco.impact_ids}
        self.assertIn(("where_used", self.bom.display_name), kinds)
        self.assertIn(("stock", self.frame_m.display_name), kinds)
        mo.action_confirm()
        eco.action_analyze()
        self.assertIn(("mo_component", mo.name), {(i.kind, i.document) for i in eco.impact_ids})
        where = eco.impact_ids.filtered(lambda i: i.kind == "where_used")
        # attribute-matched line: chosen at use time; fixed line: floating revision
        self.assertTrue("use time" in where.note or "floating revision" in where.note, where.note)

    def test_use_up_policy(self):
        self._stock(self.frame_m, 1)
        eco = self._eco(effectivity="use_up")
        eco.action_start()
        rev1 = eco.line_ids.new_tmpl_id
        self.assertEqual(rev1.engineering_revision, 1)
        self.assertEqual(rev1.plm_eco_id, eco)
        self.assertEqual(eco.state, "in_progress")
        self._release(rev1)
        self.assertEqual(eco.state, "done")
        self.assertEqual(self.frame.revision_phase_out, "use_up")
        self.assertEqual(self._mo(2), [(0, 1), (1, 1)])

    def test_immediate_policy(self):
        self._stock(self.frame_m, 1)
        eco = self._eco(effectivity="immediate")
        eco.action_start()
        self._release(eco.line_ids.new_tmpl_id)
        self.assertEqual(self.frame.revision_phase_out, "immediate")
        self.assertEqual(self._mo(1), [(1, 1)])

    def test_date_policy_and_bom_version(self):
        future = fields.Datetime.now() + timedelta(days=30)
        eco = self._eco(effectivity="date", effective_date=future,
                        bom_change_ids=[(0, 0, {"bom_id": self.bom.id, "note": "add bolt"})])
        eco.action_start()
        new_bom = eco.bom_change_ids.new_bom_id
        self.assertEqual((new_bom.state, new_bom.version, new_bom.active), ("draft", 2, False))
        new_bom.bom_line_ids = [(0, 0, {"product_id": self.bolt.id, "product_qty": 2})]
        rev1 = eco.line_ids.new_tmpl_id
        self.assertEqual(rev1.revision_effective_date, future)
        self._release(rev1)
        self.assertEqual(eco.state, "done")
        self.assertEqual(self._mo(1), [(0, 1)], "old revision until the date")
        self.assertEqual(new_bom.state, "draft", "BoM version waits for the date")
        Bom = self.env["mrp.bom"]
        self.assertEqual(Bom._bom_find(self.bike_m)[self.bike_m], self.bom)
        eco.effective_date = fields.Datetime.now() - timedelta(minutes=1)
        rev1.revision_effective_date = eco.effective_date
        self.env["plm.eco"]._cron_activate_due_bom_versions()
        self.assertEqual((new_bom.state, self.bom.state), ("active", "historical"))
        self.assertEqual(Bom._bom_find(self.bike_m)[self.bike_m], new_bom)
        self.assertEqual(self._mo(1), [(1, 1)])

    def test_bom_only_eco(self):
        eco = self.env["plm.eco"].create({"title": "Bike BoM", "effectivity": "immediate",
                                          "bom_change_ids": [(0, 0, {"bom_id": self.bom.id})]})
        eco.action_start()
        new_bom = eco.bom_change_ids.new_bom_id
        self.assertEqual(self.bom.state, "active", "current version stays active while the ECO is open")
        eco.action_done()
        self.assertEqual((eco.state, new_bom.state, self.bom.state), ("done", "active", "historical"))

    def test_close_requires_released_revisions(self):
        eco = self._eco()
        eco.action_start()
        with self.assertRaises(UserError):
            eco.action_done()
        eco.action_cancel()
        self.assertEqual(eco.state, "cancel")

    def test_manufactured_item_bom_activated_on_release(self):
        wheel = self.env["product.template"].create({"name": "ECO Wheel", "type": "consu",
                                                     "engineering_code": "ECO-WHEEL", "auto_default_code": False})
        self.env["mrp.bom"].create({"product_tmpl_id": wheel.id, "bom_line_ids": [(0, 0, {"product_id": self.bolt.id})]})
        wheel.engineering_state = "released"
        eco = self.env["plm.eco"].create({"title": "Wheel", "line_ids": [(0, 0, {"product_tmpl_id": wheel.id})]})
        eco.action_start()
        rev1 = eco.line_ids.new_tmpl_id
        bom = self.env["mrp.bom"].with_context(active_test=False).search([("product_tmpl_id", "=", rev1.id)])
        self.assertEqual(len(bom), 1)
        self._release(rev1)
        self.assertEqual(bom.state, "active")
