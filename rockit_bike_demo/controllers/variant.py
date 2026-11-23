# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request, route

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class RockitVariantController(WebsiteSaleVariantController):
    @route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, uom_id=None, **kwargs):
        # Välitetään valittu yhdistelmä kuvakarusellille (ks. product.template._get_images).
        request.update_context(rockit_image_combination=[int(c) for c in combination or []])
        return super().get_combination_info_website(product_template_id, product_id, combination, add_qty, uom_id=uom_id, **kwargs)
