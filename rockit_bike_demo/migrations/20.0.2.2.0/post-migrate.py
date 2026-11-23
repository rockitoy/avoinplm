# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""20.0.2.2.0: raakarunkoperheiden tuotemalleilta poistetaan vanhentunut koodi (esim. [RR-MAA-S] perheen nimessä).

Odoo ei tyhjennä tuotemallin tallennettua koodia, kun malliin lisätään variantteja. Ajo on toistettava.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.rockit_bike_demo import hooks


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    hooks._frame_families(env)
