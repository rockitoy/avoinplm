# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""20.0.2.3.0: monivarianttisten tuotemallien vanhentunut koodi pois (esim. [MA-VARI] Värimaali).

Juurisyy: demodata antoi Värimaali- ja Raakarunko-malleille koodin (MA-VARI, RR), joka jäi mallille,
kun variantit luotiin. Data ei enää aseta koodia; tämä ajo korjaa olemassa olevan kannan. Toistettava.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.rockit_bike_demo import hooks


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    hooks._clear_stale_template_codes(env)
