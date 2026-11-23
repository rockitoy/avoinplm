# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""20.0.2.0.0: rakenne ominaisuuksiin perustuvaksi BOMiksi (OCA mrp_bom_attribute_match).

Vanhat tietueet (20 raakarunkonimikettä, 5 värimaalinimikettä, maalattu runko Runko*-ominaisuuksineen ja
100-rivinen BOM) jäävät historiaan (valmis esimerkkitilaus S00002). Niiden XML-tunnisteet nimetään
*_v1:ksi, jotta uusi data luo uudet tietueet; post-migrate arkistoi vanhat.
"""

OLD = ["pt_maalattu_runko", "bom_maalattu_runko", "bom_polkupyora", "attr_rmalli", "attr_rkoko", "attr_rvari"]
OLD += [f"pt_ma_{c}{s}" for c in ("mus", "val", "pun", "sin", "vih") for s in ("", "_seller")]
OLD += [f"pt_rr_{m}_{z}{s}" for m in ("maa", "man", "gra", "kau", "sah") for z in ("s", "m", "l", "xl") for s in ("", "_seller")]


def migrate(cr, version):
    cr.execute(
        """UPDATE ir_model_data SET name = name || '_v1'
           WHERE module = 'rockit_bike_demo'
             AND (name = ANY(%s) OR name LIKE 'val\\_rmalli\\_%%' OR name LIKE 'val\\_rkoko\\_%%' OR name LIKE 'val\\_rvari\\_%%')""",
        (OLD,),
    )
