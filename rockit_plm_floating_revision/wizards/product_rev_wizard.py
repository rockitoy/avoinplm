# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ProductRevWizard(models.TransientModel):
    _inherit = "product.rev_wizard"

    def revise_related_attachment(self, old_product_id, new_product_id):
        """odooplm revises only the documents of the template's first variant. Revise the
        documents of every variant (each document once) and relink them."""
        revised = {}
        for variant in new_product_id.product_variant_ids:
            new_docs = self.env["ir.attachment"]
            for doc in variant.linkeddocuments:
                if doc.id not in revised:
                    try:
                        doc.new_version()
                        revised[doc.id] = doc.get_next_version() or doc
                    except Exception as error:  # keep the old document linked
                        _logger.warning("Document %s not revised: %s", doc.display_name, error)
                        revised[doc.id] = doc
                new_docs |= revised[doc.id]
            variant.linkeddocuments = [(6, 0, new_docs.ids)]
