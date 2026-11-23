# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        """Uusi (dynaaminen) variantti saa pääkuvakseen ominaisuusarvoihinsa sidotun kuvan.

        Odoo 20 asettaa variantin pääkuvan product.image-tietueista vain, kun kuvia muokataan,
        ei silloin kun variantti syntyy myöhemmin tilauksen yhteydessä.
        """
        products = super().create(vals_list)
        with_images = products.filtered(lambda p: "variant_image_ids" in p._fields and p.variant_image_ids
                                        and not p.image_variant_1920)
        if with_images:
            with_images._set_main_image_from_extra_images()
        return products
