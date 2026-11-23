# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    plm_eco_ids = fields.One2many("plm.eco", "ecr_activity_id", "ECOs")

    def action_to_eco(self):
        """odooplm: the approved change request becomes a change order. Create the ECO
        document with the request's item as the first affected item."""
        res = super().action_to_eco()
        for activity in self.filtered(lambda a: a.change_activity_type == "request" and not a.plm_eco_ids):
            activity._plm_create_eco()
        return res

    def _plm_create_eco(self):
        self.ensure_one()
        lines = []
        if self.res_model == "product.product" and self.res_id:
            template = self.env["product.product"].browse(self.res_id).product_tmpl_id
            if template.engineering_code:
                lines.append((0, 0, {"product_tmpl_id": template.id}))
        return self.env["plm.eco"].create({
            "title": self.summary or self.name or self.res_name,
            "description": self.note,
            "ecr_activity_id": self.id,
            "ecr_reference": self.summary,
            "user_id": self.user_id.id or self.env.user.id,
            "line_ids": lines,
        })

    def action_plm_open_eco(self):
        self.ensure_one()
        eco = self.plm_eco_ids[:1] or self._plm_create_eco()
        return {"type": "ir.actions.act_window", "res_model": "plm.eco", "res_id": eco.id,
                "view_mode": "form", "target": "current"}
