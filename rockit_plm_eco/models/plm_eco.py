# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError

EFFECTIVITY = [
    ("use_up", "Use up old stock first"),
    ("immediate", "Immediately on release"),
    ("date", "From a date"),
]


class PlmEco(models.Model):
    _name = "plm.eco"
    _description = "Engineering change order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char("Reference", required=True, copy=False, readonly=True, default="/")
    title = fields.Char(required=True, tracking=True)
    description = fields.Html()
    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user, tracking=True)
    ecr_activity_id = fields.Many2one(
        "mail.activity", "Change request (ECR)", ondelete="set null", copy=False,
        domain=[("activity_type_id.change_activity_type", "=", "request")])
    ecr_reference = fields.Char("ECR", copy=False, help="Summary of the change request when the ECO was made")
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In progress"),
        ("done", "Released"),
        ("cancel", "Cancelled"),
    ], default="draft", required=True, tracking=True, copy=False)
    effectivity = fields.Selection(EFFECTIVITY, default="use_up", required=True, tracking=True,
        help="Applied when the new revisions are released:\n"
        "- Use up old stock first: effective on release, free stock of the old revision is "
        "consumed first and counted in the new revision's replenishment.\n"
        "- Immediately: effective on release, the old revision is no longer used.\n"
        "- From a date: effective from the date, the old revision is used until then.")
    effective_date = fields.Datetime(tracking=True)
    line_ids = fields.One2many("plm.eco.line", "eco_id", "Affected items", copy=True)
    bom_change_ids = fields.One2many("plm.eco.bom", "eco_id", "BoM versions", copy=True)
    impact_ids = fields.One2many("plm.eco.impact", "eco_id", "Impact analysis", copy=False)
    impact_date = fields.Datetime("Analysed", readonly=True, copy=False)
    impact_count = fields.Integer(compute="_compute_counts")
    open_order_count = fields.Integer(compute="_compute_counts")

    @api.depends("impact_ids")
    def _compute_counts(self):
        for eco in self:
            eco.impact_count = len(eco.impact_ids)
            eco.open_order_count = len(eco.impact_ids.filtered(
                lambda i: i.kind in ("mo_component", "mo_product", "rfq", "po")))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("plm.eco") or "/"
        return super().create(vals_list)

    @api.constrains("effectivity", "effective_date")
    def _check_effective_date(self):
        for eco in self:
            if eco.effectivity == "date" and not eco.effective_date:
                raise UserError(self.env._("%(eco)s: give the date the change is effective from.", eco=eco.name))

    # ------------------------------------------------------------------ actions
    def action_analyze(self):
        for eco in self:
            eco.impact_ids.unlink()
            eco.impact_ids = [(0, 0, vals) for vals in eco._impact_values()]
            eco.impact_date = fields.Datetime.now()
        return True

    def action_start(self):
        """Create the new revisions and the draft BoM versions."""
        for eco in self:
            if eco.state != "draft":
                continue
            if not (eco.line_ids or eco.bom_change_ids):
                raise UserError(self.env._("%(eco)s: add the affected items or BoMs first.", eco=eco.name))
            eco.action_analyze()
            for line in eco.line_ids.filtered(lambda l: not l.new_tmpl_id):
                line._create_revision()
            for change in eco.bom_change_ids.filtered(lambda c: not c.new_bom_id):
                change._create_version()
            eco.state = "in_progress"
            eco.message_post(body=self.env._(
                "New revisions: %(revs)s. Edit them, then confirm and release each revision; "
                "the ECO closes when all are released.",
                revs=", ".join(eco.line_ids.new_tmpl_id.mapped("display_name")) or "-"))
        return True

    def action_done(self):
        """Close the ECO: every revision released, BoM versions activated."""
        for eco in self:
            pending = eco.line_ids.filtered(lambda l: l.new_tmpl_id.engineering_state != "released")
            if pending:
                raise UserError(self.env._(
                    "%(eco)s: release these revisions first: %(items)s", eco=eco.name,
                    items=", ".join(pending.new_tmpl_id.mapped("display_name") or pending.product_tmpl_id.mapped("display_name"))))
            eco._close()
        return True

    def action_cancel(self):
        for eco in self:
            if eco.state == "done":
                raise UserError(self.env._("%(eco)s is already released.", eco=eco.name))
            eco.bom_change_ids.new_bom_id.filtered(lambda b: b.state == "draft").write({"active": False})
            eco.state = "cancel"
        return True

    def action_open_orders(self):
        """Open orders still on older revisions of the released items."""
        self.ensure_one()
        released = self.line_ids.new_tmpl_id.filtered(lambda t: t.engineering_state == "released")
        if not released:
            raise UserError(self.env._("No revision of %(eco)s is released yet.", eco=self.name))
        Impact = self.env["plm.release.impact"]
        wizard = Impact.create({"product_tmpl_id": released[0].id})
        wizard.line_ids = [(0, 0, vals) for template in released for vals in template._plm_release_impact()]
        return {
            "type": "ir.actions.act_window", "res_model": Impact._name, "res_id": wizard.id,
            "view_mode": "form", "target": "new", "name": self.env._("Open orders on older revisions"),
        }

    def action_view_impact(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "plm.eco.impact", "name": self.env._("Impact analysis"),
            "view_mode": "list", "domain": [("eco_id", "=", self.id)],
            "context": {"search_default_group_kind": 1},
        }

    # ------------------------------------------------------------- effectivity
    def _effectivity_values(self):
        """(effective date for the new revision, phase-out of the older revisions)"""
        self.ensure_one()
        now = fields.Datetime.now()
        if self.effectivity == "date":
            return max(self.effective_date, now), "immediate"
        return now, "immediate" if self.effectivity == "immediate" else "use_up"

    def _on_revision_released(self, template):
        """Called when a revision of this ECO is released."""
        self.ensure_one()
        if self.state != "in_progress":
            return
        if all(line.new_tmpl_id.engineering_state == "released" for line in self.line_ids):
            self._close()

    def _close(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.effectivity != "date" or self.effective_date <= now:
            self.bom_change_ids._activate()
        self.state = "done"
        self.action_analyze()
        orders = self.open_order_count
        self.message_post(body=self.env._(
            "ECO released. Effectivity: %(eff)s%(date)s. Open orders on older revisions: %(orders)s "
            "(\"Open orders\" proposes the updates).",
            eff=dict(EFFECTIVITY)[self.effectivity],
            date=(" " + fields.Datetime.to_string(self.effective_date)) if self.effectivity == "date" else "",
            orders=orders))
        if self.ecr_activity_id and self.ecr_activity_id.exists() and self.ecr_activity_id.active:
            ecr = self.ecr_activity_id
            ecr.with_context(mail_activity_quick_update=True).action_feedback(
                feedback=self.env._("Implemented by %(eco)s", eco=self.name))

    @api.model
    def _cron_activate_due_bom_versions(self):
        """Activate the BoM versions of released ECOs whose effective date is reached."""
        due = self.search([("state", "=", "done"), ("effectivity", "=", "date"),
                           ("effective_date", "<=", fields.Datetime.now())])
        due.bom_change_ids.filtered(lambda c: c.new_bom_id.state == "draft")._activate()

    # ----------------------------------------------------------------- impact
    def _impact_values(self):
        self.ensure_one()
        values = []
        for line in self.line_ids:
            values += line._impact_values()
        for change in self.bom_change_ids:
            values += change._impact_values()
        return values


class PlmEcoLine(models.Model):
    _name = "plm.eco.line"
    _description = "ECO affected item"

    eco_id = fields.Many2one("plm.eco", required=True, ondelete="cascade", index=True)
    product_tmpl_id = fields.Many2one("product.template", "Item", required=True,
                                      domain=[("engineering_code", "!=", False)])
    engineering_code = fields.Char(related="product_tmpl_id.engineering_code")
    current_revision = fields.Integer(related="product_tmpl_id.engineering_revision", string="Rev.")
    revise_documents = fields.Boolean("Revise documents", default=True)
    new_tmpl_id = fields.Many2one("product.template", "New revision", readonly=True, copy=False)
    new_revision = fields.Integer(related="new_tmpl_id.engineering_revision", string="New rev.")
    new_state = fields.Selection(related="new_tmpl_id.engineering_state", string="New revision state")
    note = fields.Char("Change")

    def _create_revision(self):
        self.ensure_one()
        template = self.product_tmpl_id
        if template.engineering_state != "released":
            raise UserError(self.env._(
                "%(item)s is not released (state %(state)s): a new revision can only be made "
                "from a released revision.", item=template.display_name, state=template.engineering_state))
        variant = template.product_variant_ids[:1]
        wizard = self.env["product.rev_wizard"].with_context(
            active_id=variant.id, active_model="product.product").create({"reviseDocument": self.revise_documents})
        wizard.action_create_new_revision_by_server()
        new = template.get_next_version()
        if not new or new == template:
            raise UserError(self.env._("No new revision was created for %(item)s.", item=template.display_name))
        effective_date, _phase_out = self.eco_id._effectivity_values()
        new.write({"plm_eco_id": self.eco_id.id,
                   "revision_effective_date": effective_date if self.eco_id.effectivity == "date" else False})
        self.new_tmpl_id = new

    def _impact_values(self):
        self.ensure_one()
        template = self.product_tmpl_id
        revisions = template._plm_revisions()
        variants = revisions.with_context(active_test=False).product_variant_ids
        base = {"eco_line_id": self.id, "item": template.engineering_code}
        values = []
        BomLine = self.env["mrp.bom.line"]
        fixed = BomLine.search([("product_id", "in", variants.ids)])
        for bom_line in fixed:
            values.append(dict(base, kind="where_used", bom_id=bom_line.bom_id.id, product_id=bom_line.product_id.id,
                               quantity=bom_line.product_qty, document=bom_line.bom_id.display_name,
                               note=self.env._("Fixed line, floating revision") if bom_line.float_revision
                               else self.env._("Fixed line, exact revision: update the BoM")))
        matched = BomLine
        # attribute-matched lines and component families (configurator modules, optional)
        if "component_template_id" in BomLine._fields:
            matched |= BomLine.search([("component_template_id", "in", revisions.ids)])
        if "component_family_ids" in BomLine._fields:
            matched |= BomLine.search([("component_family_ids", "in", revisions.ids)])
        for bom_line in matched - fixed:
            how = self.env._("Component family") if "component_family_ids" in bom_line._fields and bom_line.component_family_ids else self.env._("Attribute match line")
            values.append(dict(base, kind="where_used", bom_id=bom_line.bom_id.id, quantity=bom_line.product_qty,
                               document=bom_line.bom_id.display_name,
                               note=self.env._("%(how)s: variant and revision chosen at use time", how=how)))
        for variant in variants.filtered(lambda v: v.is_storable):
            if variant.qty_available or variant.incoming_qty or variant.outgoing_qty:
                values.append(dict(base, kind="stock", product_id=variant.id, quantity=variant.qty_available,
                                   free_qty=variant.free_qty, incoming_qty=variant.incoming_qty,
                                   outgoing_qty=variant.outgoing_qty, document=variant.display_name))
        moves = self.env["stock.move"].search([
            ("raw_material_production_id.state", "in", ("draft", "confirmed", "progress", "to_close")),
            ("product_id", "in", variants.ids), ("state", "not in", ("done", "cancel"))])
        for move in moves:
            production = move.raw_material_production_id
            values.append(dict(base, kind="mo_component", production_id=production.id, product_id=move.product_id.id,
                               quantity=move.product_uom_qty, document=production.name, date=production.date_start,
                               note=production.state))
        for production in self.env["mrp.production"].search([
                ("product_id", "in", variants.ids), ("state", "in", ("draft", "confirmed", "progress", "to_close"))]):
            values.append(dict(base, kind="mo_product", production_id=production.id, product_id=production.product_id.id,
                               quantity=production.product_qty, document=production.name, date=production.date_start,
                               note=production.state))
        for line in self.env["purchase.order.line"].search([
                ("product_id", "in", variants.ids), ("order_id.state", "in", ("draft", "sent", "to approve", "purchase"))]):
            if line.order_id.state == "purchase" and line.uom_id.compare(line.qty_received, line.product_qty) >= 0:
                continue
            values.append(dict(base, kind="po" if line.order_id.state == "purchase" else "rfq",
                               purchase_line_id=line.id, product_id=line.product_id.id, quantity=line.product_qty,
                               document=line.order_id.name, date=line.date_planned, note=line.partner_id.name))
        return values


class PlmEcoBom(models.Model):
    _name = "plm.eco.bom"
    _description = "ECO BoM version change"

    eco_id = fields.Many2one("plm.eco", required=True, ondelete="cascade", index=True)
    bom_id = fields.Many2one("mrp.bom", "BoM", required=True, domain=[("state", "=", "active")])
    product_tmpl_id = fields.Many2one(related="bom_id.product_tmpl_id")
    version = fields.Integer(related="bom_id.version", string="Version")
    new_bom_id = fields.Many2one("mrp.bom", "New version", readonly=True, copy=False)
    new_version = fields.Integer(related="new_bom_id.version", string="New version no.")
    new_state = fields.Selection(related="new_bom_id.state", string="New version state")
    note = fields.Char("Change")

    def _create_version(self):
        self.ensure_one()
        new_bom = self.bom_id.with_context(active_test=False)._copy_bom()
        new_bom.write({"active": False, "state": "draft", "plm_eco_id": self.eco_id.id})
        self.new_bom_id = new_bom

    def _activate(self):
        for change in self.filtered(lambda c: c.new_bom_id and c.new_bom_id.state == "draft"):
            change.new_bom_id.button_activate()
            if change.bom_id.state == "active":
                change.bom_id.button_historical()

    def _impact_values(self):
        self.ensure_one()
        bom = self.bom_id
        base = {"eco_bom_id": self.id, "item": bom.product_tmpl_id.display_name}
        values = []
        # open sales: only when the Sales app is installed (not a dependency)
        SaleLine = self.env["sale.order.line"] if "sale.order.line" in self.env else None
        sale_lines = [] if SaleLine is None else SaleLine.search([
            ("product_id.product_tmpl_id", "=", bom.product_tmpl_id.id),
            ("order_id.state", "=", "sale")]).filtered(lambda l: l.qty_delivered < l.product_uom_qty)
        for line in sale_lines:
            values.append(dict(base, kind="so", product_id=line.product_id.id, quantity=line.product_uom_qty,
                               document=line.order_id.name, date=line.order_id.commitment_date or line.order_id.date_order,
                               note=self.env._("Open sale: produced with the BoM version active at the MO")))
        for production in self.env["mrp.production"].search([
                ("bom_id", "=", bom.id), ("state", "in", ("draft", "confirmed", "progress", "to_close"))]):
            values.append(dict(base, kind="mo_product", production_id=production.id, product_id=production.product_id.id,
                               quantity=production.product_qty, document=production.name, date=production.date_start,
                               note=self.env._("Uses BoM version %(v)s", v=bom.version)))
        return values


class PlmEcoImpact(models.Model):
    _name = "plm.eco.impact"
    _description = "ECO impact analysis line"
    _order = "kind, item, document, id"

    eco_id = fields.Many2one("plm.eco", required=True, ondelete="cascade", index=True)
    eco_line_id = fields.Many2one("plm.eco.line", ondelete="cascade")
    eco_bom_id = fields.Many2one("plm.eco.bom", ondelete="cascade")
    kind = fields.Selection([
        ("where_used", "Where used"),
        ("stock", "Stock"),
        ("mo_component", "MO component"),
        ("mo_product", "MO producing it"),
        ("rfq", "RFQ"),
        ("po", "Confirmed PO"),
        ("so", "Open sale"),
    ], required=True)
    item = fields.Char()
    document = fields.Char()
    bom_id = fields.Many2one("mrp.bom", "BoM")
    production_id = fields.Many2one("mrp.production")
    purchase_line_id = fields.Many2one("purchase.order.line")
    product_id = fields.Many2one("product.product")
    revision = fields.Char(related="product_id.plm_revision", string="Rev.")
    quantity = fields.Float(digits="Product Unit")
    free_qty = fields.Float("Free", digits="Product Unit")
    incoming_qty = fields.Float("Incoming", digits="Product Unit")
    outgoing_qty = fields.Float("Outgoing", digits="Product Unit")
    date = fields.Datetime()
    note = fields.Char()
