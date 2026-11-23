# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_images(self):
        """Verkkokaupan kuvakaruselli dynaamisille varianteille.

        Odoo 20 näyttää ominaisuusarvoihin sidotut kuvat (product.image.attribute_value_ids) vain,
        kun variantti on jo olemassa. Dynaamisilla ominaisuuksilla variantti syntyy vasta tilattaessa,
        joten valitulle yhdistelmälle näytetään tässä sitä vastaavat kuvat (esim. Malli = Maasto).
        """
        images = super()._get_images()
        ptav_ids = self.env.context.get("rockit_image_combination")
        if not ptav_ids or len(self) != 1 or not self.product_template_image_ids:
            return images
        combination = self.env["product.template.attribute.value"].browse(ptav_ids)

        def matches(image):
            values = image.attribute_value_ids
            return all(combination & values.filtered(lambda v, line=line: v.attribute_line_id == line)
                       for line in values.attribute_line_id)

        all_images = self.product_template_image_ids.sorted("sequence")
        specific = all_images.filtered(lambda i: i.has_attribute_value and matches(i))
        return (specific + all_images.filtered(lambda i: not i.has_attribute_value)) or images
