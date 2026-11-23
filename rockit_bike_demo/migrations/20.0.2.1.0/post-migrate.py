# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""20.0.2.1.0: raakarunko malliperheiksi RR-MAA, RR-MAN, RR-GRA, RR-KAU, RR-SAH (ks. hooks._frame_families).

Yhteisen tuotemallin "Raakarunko (muut mallit)" variantit arkistoidaan koodilla …-VANHA, uudet variantit saavat
samat koodit RR-<malli>-<koko>. RR-GRA:lle (luotu 22.11.2026 ilman kuvia) lisätään kuvat ja materiaali.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.rockit_bike_demo import hooks


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    hooks._frame_families(env)
    hooks._ecr(env)
