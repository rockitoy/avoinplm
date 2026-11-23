# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""20.0.2.5.0: konfiguroitaville tuotemalleille koodin etuliite (Polkupyörä PP-, Maalattu runko MR-)
ja ominaisuusarvoille koodit, jotta varianteilla on luettava koodi (PP-GRA-MUS-M-PER).

Data on noupdate-tilassa, joten olemassa oleva kanta korjataan tässä. Vain koodittomat variantit
saavat koodin; käsin annetut koodit (RR-*, MA-*) pysyvät. Toistettava.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.rockit_bike_demo import hooks


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    hooks._variant_code_prefixes(env)
