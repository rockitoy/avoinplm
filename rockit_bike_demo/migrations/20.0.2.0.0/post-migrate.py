# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Arkistoi vanhat (v1) tietueet ja luo uusi rakenne hookin vaiheilla. Ks. pre-migrate.py."""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.rockit_bike_demo import hooks

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    imd = env["ir.model.data"].search([("module", "=", "rockit_bike_demo"), ("name", "=like", "%\\_v1")])
    old_tmpls = env["product.template"].with_context(active_test=False).browse(
        imd.filtered(lambda d: d.model == "product.template").mapped("res_id")).exists()
    old_boms = env["mrp.bom"].with_context(active_test=False).browse(
        imd.filtered(lambda d: d.model == "mrp.bom").mapped("res_id")).exists()
    old_products = old_tmpls.with_context(active_test=False).product_variant_ids
    # Varastosaldot nollaan (inventaario) ja täydennyssäännöt pois vanhoilta nimikkeiltä
    quants = env["stock.quant"].search([("product_id", "in", old_products.ids), ("location_id.usage", "=", "internal")])
    for q in quants.filtered(lambda q: q.quantity):
        q.with_context(inventory_mode=True).write({"inventory_quantity": 0})
        q.with_context(inventory_mode=True).action_apply_inventory()
    env["stock.warehouse.orderpoint"].with_context(active_test=False).search(
        [("product_id", "in", old_products.ids)]).unlink()
    old_boms.write({"active": False})
    for t in old_tmpls:
        try:
            with env.cr.savepoint():
                t.write({"active": False})
        except Exception as e:  # pragma: no cover
            _logger.warning("v1-nimikkeen %s arkistointi epäonnistui: %s", t.display_name, e)
    _logger.info("rockit_bike_demo 2.0: arkistoitu %s nimikettä ja %s BOMia", len(old_tmpls), len(old_boms))
    sale_tax = env.company.account_sale_tax_id
    hooks._taxes_and_flags(env, sale_tax)
    hooks._component_variants(env)
    hooks._frames_plm(env)
    hooks._boms(env)
    from odoo.addons.rockit_bike_demo.tools_data import STOCK_PARTS
    hooks._stock(env, dict(STOCK_PARTS))
    hooks._ecr(env)
    hooks._images(env)
