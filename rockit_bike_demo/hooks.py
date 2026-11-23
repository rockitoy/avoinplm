# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Asennuksen jälkeinen alustus polkupyörädemolle.

XML:llä ei voi viitata tuotteen ominaisuusarvoihin (product.template.attribute.value),
joten BOMit, täydennyssäännöt, alkusaldot ja PLM-tila tehdään täällä. Jokainen vaihe
tarkistaa ensin, onko se jo tehty: hookin voi ajaa uudelleen (odoo shell:
``from odoo.addons.rockit_bike_demo.hooks import post_init_hook; post_init_hook(env)``).
"""
import datetime
import logging

from markupsafe import Markup

_logger = logging.getLogger(__name__)
M = "rockit_bike_demo"

MODELS = ["MAA", "MAN", "GRA", "KAU", "SAH"]
COLORS = ["MUS", "VAL", "PUN", "SIN", "VIH"]
SIZES = ["S", "M", "L", "XL"]
FRAME_MATERIAL = {"MAA": "Alumiini 6061-T6", "MAN": "Alumiini 6061-T6", "GRA": "Alumiini 6061-T6",
                  "KAU": "Teräs Cr-Mo 4130", "SAH": "Alumiini 6061-T6, vahvistettu"}

# Pyörän BOM: (koodi, määrä, {ominaisuus: [arvot]}) – tyhjä ehto = kaikille
BIKE_LINES = []
for _m in MODELS:
    BIKE_LINES += [(f"HA-{_m}", 1, {"malli": [_m]}), (f"KS-{_m}", 1, {"malli": [_m]}), (f"RE-{_m}", 1, {"malli": [_m]})]
BIKE_LINES += [
    ("VS-PER", 1, {"vaiht": ["PER"]}), ("VS-PRE", 1, {"vaiht": ["PRE"]}),
    ("JA-VAN", 1, {"malli": ["KAU"]}), ("JA-LEV", 1, {"malli": ["MAA", "MAN", "GRA", "SAH"]}),
    ("OH-DROP", 1, {"malli": ["MAN", "GRA"]}), ("OH-SUO", 1, {"malli": ["MAA", "KAU", "SAH"]}),
    ("SA-SAT", 1, {}), ("SA-TOL", 1, {}), ("PO-ALU", 1, {}),
    ("EV-MOOT", 1, {"malli": ["SAH"]}), ("EV-AKKU", 1, {"malli": ["SAH"]}), ("EV-NAYT", 1, {"malli": ["SAH"]}),
    ("PI-VAIJ", 1, {}), ("PI-PULT", 1, {}), ("PI-LAAT", 1, {}),
]
CHECKLIST = Markup(
    "<p><b>Tarkistuslista ennen pakkausta</b> (kuittaa työvaiheen ohjeesta):</p><ul>"
    "<li>Kiristysmomentit: stemmi 5 Nm, satulatolppa 6 Nm, polkimet 35 Nm, kammet valmistajan ohjeen mukaan</li>"
    "<li>Vaihteet: kaikki vaihteet vaihtuvat kuormitettuna, rajaruuvit säädetty</li>"
    "<li>Jarrut: jarrukahvan vapaaliike, levyt/vanteet puhtaat, jarrutus koeajossa</li>"
    "<li>Kiekot: suoruus ±0,5 mm, renkaiden paineet suosituksen mukaan</li>"
    "<li>Sähköpyörä: akun lataus &gt; 50 %, näytön ohjelmistoversio, avustustasot toimivat</li>"
    "<li>Maalipinta: ei valumia, roiskeita tai kolhuja</li>"
    "<li>Koeajo 200 m ja sarjanumero kirjattu</li></ul>")

# Odoo CE 20:n työvaiheella ei ole ohjekenttää: ohjeet BOMin huomautuksiin (näkyvät valmistustilauksella)
FRAME_NOTE = Markup(
    "<p><b>Työohje, maalattu runko</b></p><ol>"
    "<li>Esikäsittely: pese runko, poista rasva ja hio hitsaussaumat. Teippaa laakeripesät ja kierteet.</li>"
    "<li>Pohjamaalaus: epoksipohjamaali 0,3 l, kalvonpaksuus 40–60 µm.</li>"
    "<li>Värimaalaus ja lakkaus: tilauksen värin mukainen maali 0,4 l, 2K-kirkaslakka 0,3 l (musta matta: mattalakka).</li>"
    "<li>Kuivaus uunissa 45 min 60 °C. Runko jäähtyy ennen siirtoa kokoonpanoon.</li></ol>")
BIKE_NOTE = Markup(
    "<p><b>Työohje, polkupyörä</b></p><ol>"
    "<li>Kokoonpano: ohjainlaakeri, haarukka ja ohjaamo, kiekot ja renkaat, voimansiirto, jarrut, satula ja polkimet.</li>"
    "<li>Sähkömalli: keskimoottori, akun kiinnike ja akku, näyttö ja johtosarja, ohjelmistopäivitys ja diagnostiikka.</li>"
    "<li>Säätö ja laadunvarmistus tarkistuslistan mukaan (alla).</li>"
    "<li>Pakkaus: ohjaustanko ja polkimet irti, suojamuovit, käyttöohje ja takuukortti laatikkoon.</li></ol>")


def _ref(env, name):
    return env.ref(f"{M}.{name}")


def _tmpl(env, code):
    return env.ref(f"{M}.pt_{code.lower().replace('-', '_')}")


def _set_xmlid(env, record, name):
    env["ir.model.data"].create({"module": M, "name": name, "model": record._name, "res_id": record.id, "noupdate": True})


def _settings(env):
    company = env.company
    cfg = env["res.config.settings"].create({})
    for flag in ("group_product_variant", "group_mrp_routings", "group_uom"):
        if flag in cfg._fields:
            cfg[flag] = True
    cfg.execute()
    # Ei tekstiviestivahvistusta toimituksen kuittauksessa (demossa ei SMS-tiliä)
    for f, v in (("stock_move_sms_validation", False), ("has_received_warning_stock_sms", True)):
        if f in company._fields:
            company[f] = v
    mto = env.ref("stock.route_warehouse0_mto")
    if not mto.active:
        mto.with_context(active_test=False).action_unarchive()
    env["stock.rule"].with_context(active_test=False).search([("route_id", "=", mto.id)]).write({"active": True})
    # Kuluttajahinnat sisältävät ALV:n: myynnin 25,5 % vero hintaan sisältyväksi
    sale_tax = company.account_sale_tax_id
    if sale_tax and sale_tax.price_include_override != "tax_included":
        sale_tax.price_include_override = "tax_included"
    # Hinnasto seuraa yrityksen valuuttaa (vaihdettiin USD -> EUR, kun tilikartta vaihtui suomalaiseen)
    env["product.pricelist"].with_context(active_test=False).search(
        [("currency_id", "!=", company.currency_id.id)]).write({"currency_id": company.currency_id.id})
    for website in env["website"].search([("company_id", "=", company.id)]):
        website.show_line_subtotals_tax_selection = "tax_included"
    wire = env["payment.provider"].search([("code", "=", "custom"), ("custom_mode", "=", "wire_transfer")], limit=1) \
        if "custom_mode" in env["payment.provider"]._fields else env["payment.provider"].search([("name", "=", "Tilisiirto")], limit=1)
    if wire:
        vals = {"is_published": True}
        if "state" in wire._fields:
            vals["state"] = "enabled"
        wire.write(vals)
    return sale_tax


def _taxes_and_flags(env, sale_tax):
    company = env.company
    purchase_tax = company.account_purchase_tax_id
    prods = env["product.template"].search([("categ_id", "child_of", _ref(env, "categ_root").id)])
    prods.write({"taxes_id": [(6, 0, sale_tax.ids)], "supplier_taxes_id": [(6, 0, purchase_tax.ids)]})


def _product(env, code):
    """Nimike tai variantti sisäisellä koodilla (raakarungot ja värimaalit ovat variantteja)."""
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def _variant(tmpl, values):
    """Hae tai luo variantti ominaisuusarvoista {attr_key: value_key} (dynaamiset ominaisuudet)."""
    ptavs = tmpl.env["product.template.attribute.value"]
    for a, k in values.items():
        ptavs |= _ptav(tmpl, a, [k])
    return tmpl._create_product_variant(ptavs)


def _component_variants(env):
    """Raakarungon (Malli × Koko) ja värimaalin (Väri) variantit, koodit, kustannukset ja toimittajahinnat.

    Ominaisuudet ovat dynaamisia (pyörän konfiguraattori), joten variantit luodaan tässä. Malli-arvon
    lisähinta koskee vain myytävää pyörää: komponenttien variaatiolisähinnat nollataan.
    """
    from .tools_data import FRAME_COST
    frame, paint = _ref(env, "pt_raakarunko"), _ref(env, "pt_varimaali")
    seller_model = env["product.supplierinfo"]
    _frame_codes(env)
    for m in (MODELS if frame.active else []):  # jaettu malliperheisiin: ks. _frame_families
        for s in SIZES:
            v = _variant(frame, {"malli": m, "koko": s})
            if not seller_model.search([("product_id", "=", v.id)]):
                seller_model.create({"partner_id": _ref(env, "vendor_runko").id, "product_tmpl_id": frame.id,
                                     "product_id": v.id, "price": FRAME_COST[m], "delay": 21, "min_qty": 1})
    for c in COLORS:
        v = _variant(paint, {"vari": c})
        if v.default_code != f"MA-{c}":
            v.write({"default_code": f"MA-{c}", "standard_price": 45})
    for t in (frame, paint, _ref(env, "pt_maalattu_runko")):
        t.attribute_line_ids.product_template_value_ids.filtered("price_extra").write({"price_extra": 0})


def _frame_codes(env):
    """Raakarungon varianttikoodit RR-<malli>-<koko>. plm_auto_internalref kopioi tuotemallin koodin (RR_0)
    varianteille PLM-tilan muuttuessa, joten koodit asetetaan uudelleen sen jälkeen."""
    from .tools_data import FRAME_COST
    frame = _ref(env, "pt_raakarunko")
    if not frame.active:
        return  # jaettu malliperheisiin (_frame_families); muuten arkistoidut variantit palautuisivat
    if "auto_default_code" in frame._fields and frame.auto_default_code:
        frame.auto_default_code = False  # muuten PLM kirjoittaa varianttien koodiksi RR_0
    for m in MODELS:
        for s in SIZES:
            v = _variant(frame, {"malli": m, "koko": s})
            if v.default_code != f"RR-{m}-{s}":
                v.write({"default_code": f"RR-{m}-{s}"})
            if not v.standard_price:
                v.standard_price = FRAME_COST[m]


def _frames_plm(env):
    """Raakarunko on PLM-nimike: tunnus, materiaali, revisio 0, tila vapautettu."""
    t = _ref(env, "pt_raakarunko")
    if not t.active:
        return
    if not t.engineering_code:
        t.write({"engineering_code": "RR", "engineering_revision": 0,
                 "engineering_material": "Alumiini 6061-T6 (Kaupunki: teräs Cr-Mo 4130)"})
    v = t.product_variant_ids[:1]
    if v.engineering_state == "draft":
        v.action_confirm()
    if v.engineering_state == "confirmed":
        v.action_release()
    _frame_codes(env)


def _ptav(tmpl, attr_key, val_keys):
    vals = [f"{M}.val_{attr_key}_{k.lower()}" for k in val_keys]
    pav_ids = [tmpl.env.ref(x).id for x in vals]
    return tmpl.valid_product_template_attribute_line_ids.product_template_value_ids.filtered(
        lambda p: p.product_attribute_value_id.id in pav_ids)


def _boms(env):
    """Kaksitasoinen BOM, jossa komponentit valitaan ominaisuuksien perusteella (OCA mrp_bom_attribute_match).

    - Polkupyörä: 1 rivi "Maalattu runko" (täsmää Malli + Koko + Väri) + osat mallin/vaihteiston mukaan.
    - Maalattu runko: 1 rivi "Raakarunko" (täsmää Malli + Koko), pohjamaali, "Värimaali" (täsmää Väri), lakka.
    """
    if env.ref(f"{M}.bom_maalattu_runko", raise_if_not_found=False):
        return
    frame = _ref(env, "pt_maalattu_runko")
    bike = _ref(env, "pt_polkupyora")
    wc = {k: _ref(env, f"wc_{k}") for k in ("esik", "maal", "koko", "saato", "pakk")}
    lines = [
        (0, 0, {"component_template_id": _ref(env, "pt_raakarunko").id, "product_qty": 1}),
        (0, 0, {"product_id": _product(env, "MA-POHJA").id, "product_qty": 0.3}),
        (0, 0, {"component_template_id": _ref(env, "pt_varimaali").id, "product_qty": 0.4}),
        (0, 0, {"product_id": _product(env, "MA-LAKKA").id, "product_qty": 0.3}),
    ]
    ops = [
        (0, 0, {"name": "Pesu, rasvanpoisto ja hionta", "workcenter_id": wc["esik"].id, "time_cycle_manual": 20, "sequence": 10}),
        (0, 0, {"name": "Pohjamaalaus", "workcenter_id": wc["maal"].id, "time_cycle_manual": 15, "sequence": 20}),
        (0, 0, {"name": "Värimaalaus ja lakkaus", "workcenter_id": wc["maal"].id, "time_cycle_manual": 25, "sequence": 30}),
        (0, 0, {"name": "Kuivaus uunissa (60 °C)", "workcenter_id": wc["maal"].id, "time_cycle_manual": 45, "sequence": 40}),
    ]
    b1 = env["mrp.bom"].create({"product_tmpl_id": frame.id, "type": "normal", "product_qty": 1, "code": "MR / B",
                                "bom_line_ids": lines, "operation_ids": ops, "note": FRAME_NOTE})
    _set_xmlid(env, b1, "bom_maalattu_runko")
    lines = [(0, 0, {"component_template_id": frame.id, "product_qty": 1})]
    for code, qty, cond in BIKE_LINES:
        ptavs = env["product.template.attribute.value"]
        for a, ks in cond.items():
            ptavs |= _ptav(bike, a, ks)
        lines.append((0, 0, {"product_id": _tmpl(env, code).product_variant_id.id, "product_qty": qty,
                             "bom_product_template_attribute_value_ids": [(6, 0, ptavs.ids)]}))
    ops = [
        (0, 0, {"name": "Kokoonpano", "workcenter_id": wc["koko"].id, "time_cycle_manual": 75, "sequence": 10}),
        (0, 0, {"name": "Sähkövetojärjestelmän asennus", "workcenter_id": wc["koko"].id, "time_cycle_manual": 30, "sequence": 15,
                "bom_product_template_attribute_value_ids": [(6, 0, _ptav(bike, "malli", ["SAH"]).ids)]}),
        (0, 0, {"name": "Säätö ja laadunvarmistus", "workcenter_id": wc["saato"].id, "time_cycle_manual": 25, "sequence": 20}),
        (0, 0, {"name": "Pakkaus", "workcenter_id": wc["pakk"].id, "time_cycle_manual": 15, "sequence": 30}),
    ]
    b2 = env["mrp.bom"].create({"product_tmpl_id": bike.id, "type": "normal", "product_qty": 1, "code": "PP / B",
                                "bom_line_ids": lines, "operation_ids": ops, "note": BIKE_NOTE + CHECKLIST})
    _set_xmlid(env, b2, "bom_polkupyora")


def _stock(env, initial):
    wh = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
    loc = wh.lot_stock_id
    OP = env["stock.warehouse.orderpoint"].with_context(active_test=False)  # arkistoitu = siirretty uudelle revisiolle
    for code, (mn, mx, start) in initial.items():
        p = _product(env, code)
        if not p:
            _logger.warning("Varastoitavaa nimikettä %s ei löydy", code)
            continue
        if not OP.search([("product_id", "=", p.id)]):
            OP.create({"product_id": p.id, "location_id": loc.id, "warehouse_id": wh.id,
                       "product_min_qty": mn, "product_max_qty": mx, "trigger": "auto"})
        if not env["stock.quant"].search([("product_id", "=", p.id), ("location_id", "=", loc.id)]):
            env["stock.quant"].with_context(inventory_mode=True).create(
                {"product_id": p.id, "location_id": loc.id, "inventory_quantity": start})._apply_inventory()


def _archive_valves(env):
    """Vanha RV-kuulaventtiilidemo arkistoon (ei poisteta: PLM estää vapautettujen poiston)."""
    PT = env["product.template"].with_context(active_test=False)
    tmpls = PT.search([("active", "=", True), "|", ("engineering_code", "=like", "RV%"), ("default_code", "=like", "RV%")])
    if not tmpls:
        return
    boms = env["mrp.bom"].search([("product_tmpl_id", "in", tmpls.ids)])
    boms.write({"active": False})
    acts = env["mail.activity"].search([("summary", "=like", "ECR-000%")])
    for a in acts:
        try:
            with env.cr.savepoint():
                a.write({"active": False})
        except Exception as e:  # pragma: no cover
            _logger.warning("ECR-aktiviteetin %s arkistointi epäonnistui: %s", a.summary, e)
    for t in tmpls:
        try:
            with env.cr.savepoint():
                t.write({"active": False})
        except Exception as e:  # pragma: no cover - raportoidaan lokiin
            _logger.warning("RV-nimikkeen %s arkistointi epäonnistui: %s", t.display_name, e)
    env["res.partner"].search([("ref", "=like", "DEMO-V0%")]).write({"active": False})
    cat = env["product.category"].search([("name", "=", "RV-kuulaventtiilit")])
    if cat:
        cat.name = "RV-kuulaventtiilit (arkistoitu demo)"


def _demo_user(env):
    user = env["res.users"].search([("login", "=", "demo")], limit=1)
    if not user:
        return
    groups = env["res.groups"]
    for x in ("base.group_allow_export", "sales_team.group_sale_salesman_all_leads", "purchase.group_purchase_user", "account.group_account_invoice",
              "mrp.group_mrp_user", "stock.group_stock_user"):
        g = env.ref(x, raise_if_not_found=False)
        if g:
            groups |= g
    field = "group_ids" if "group_ids" in user._fields else "groups_id"
    user.write({field: [(4, g.id) for g in groups]})


def _ecr(env):
    frame = _product(env, "RR-GRA-M")
    Act = env["mail.activity"].with_context(active_test=False)
    existing = Act.search([("summary", "=like", "ECR-0101%")], limit=1)
    if existing:
        # Rakennemuutoksen jälkeen muutospyyntö osoittaa uuteen raakarunkonimikkeeseen
        if existing.res_model == "product.product" and existing.res_id != frame.id:
            existing.write({"res_id": frame.id})
        return
    a = Act.create({
        "activity_type_id": env.ref("activity_validation.mail_activity_change_request").id,
        "res_model_id": env["ir.model"]._get("product.product").id, "res_id": frame.id,
        "user_id": env.ref("base.user_admin").id,
        "date_deadline": datetime.date.today() + datetime.timedelta(days=14),
        "summary": "ECR-0101 Gravel-rungon geometria: leveämpi rengastila (rev 1)",
        "note": Markup("<p>Asiakaspalaute: gravel-mallin 700×40-renkaille jää liian vähän mutavaraa. Ehdotus: takahaarukan "
                       "ja haarukan rengastila 45 mm:iin. Vaikutus: raakarungon gravel-variantit RR-GRA-S/M/L/XL rev 1, toimittajan "
                       "Runkopaja Demo Oy hinnan ja toimitusajan tarkistus, pyörän BOM pysyy ennallaan.</p>"),
    })
    if hasattr(a, "action_in_progress"):
        a.action_in_progress()


def pre_init_hook(env):
    """MTO-reitti on Odoo 20:ssä oletuksena arkistoitu; XML-data viittaa siihen."""
    mto = env.ref("stock.route_warehouse0_mto", raise_if_not_found=False)
    if mto and not mto.active:
        mto.with_context(active_test=False).action_unarchive()
        env["stock.rule"].with_context(active_test=False).search([("route_id", "=", mto.id)]).write({"active": True})


# Tuotekuvat (static/img/products/*.jpg): koodi -> kuva. Kuvat on generoitu, ei tuotemerkkejä.
MODEL_IMG = {"MAA": "maa", "MAN": "man", "GRA": "gra", "KAU": "kau", "SAH": "sah"}
FORK_IMG = {"MAA": "ha_jousto", "SAH": "ha_jousto", "MAN": "ha_hiili", "GRA": "ha_hiili", "KAU": "ha_teras"}
WHEEL_IMG = {"MAA": "ks_mtb", "SAH": "ks_mtb", "MAN": "ks_road", "GRA": "ks_road", "KAU": "ks_city"}
TYRE_IMG = {"MAA": "re_mtb", "SAH": "re_mtb", "MAN": "re_road", "GRA": "re_gravel", "KAU": "re_city"}
BIKE_GALLERY = [("Maasto", "bike_maa"), ("Maantie", "bike_man"), ("Gravel, punainen", "bike_gra_pun"),
                ("Kaupunki", "bike_kau"), ("Sähkö", "bike_sah"), ("Gravel, musta matta", "bike_gra_mus"),
                ("Gravel, valkoinen", "bike_gra_val"), ("Gravel, sininen", "bike_gra_sin"), ("Gravel, vihreä", "bike_gra_vih")]


def _read_image(name):
    """static/img/products/<name>.jpg base64-merkkijonona (Odoo 20 ei hyväksy raakoja bytes-arvoja)."""
    import base64
    from odoo.tools.misc import file_path
    try:
        with open(file_path(f"rockit_bike_demo/static/img/products/{name}.jpg"), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return False


def _attr_images(env, tmpl, specs):
    """Odoo 20 -vakiotapa: product.image + attribute_value_ids. Variantti saa automaattisesti kuvan,
    jonka ominaisuusarvot täsmäävät (osittainenkin täsmäys riittää, esim. pelkkä Malli)."""
    tmpl.product_template_image_ids.unlink()
    vals = []
    for seq, (name, img, pav_xmlids) in enumerate(specs, start=1):
        pavs = env["product.attribute.value"].browse([_ref(env, x).id for x in pav_xmlids])
        ptavs = tmpl.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id in pavs)
        vals.append({"name": name, "sequence": seq, "image_1920": _read_image(img),
                     "product_tmpl_id": tmpl.id, "attribute_value_ids": [(6, 0, ptavs.ids)]})
    env["product.image"].create(vals)


def _images(env):
    def put(code, name):
        img = _read_image(name)
        if img:
            _tmpl(env, code).image_1920 = img
    for m, k in MODEL_IMG.items():
        put(f"HA-{m}", FORK_IMG[m])
        put(f"KS-{m}", WHEEL_IMG[m])
        put(f"RE-{m}", TYRE_IMG[m])
    for code in ("VS-PER", "VS-PRE", "JA-VAN", "JA-LEV", "OH-DROP", "OH-SUO", "SA-SAT", "SA-TOL", "PO-ALU",
                 "EV-MOOT", "EV-AKKU", "EV-NAYT", "MA-POHJA", "MA-LAKKA",
                 "PI-VAIJ", "PI-PULT", "PI-LAAT", "LV-LOKA", "LV-TELI", "LV-VALO", "LV-LUKKO"):
        put(code, code.lower().replace("-", "_"))
    if "product.image" not in env:
        return
    # Pyörä: gravel värin mukaan, muut mallit yhdellä kuvalla. Ensimmäinen kuva = tuotteen pääkuva.
    bike_specs = [("Gravel, punainen", "bike_gra_pun", ["val_malli_gra", "val_vari_pun"])]
    for m, n in (("maa", "Maasto"), ("man", "Maantie"), ("kau", "Kaupunki"), ("sah", "Sähkö")):
        bike_specs.append((n, f"bike_{m}", [f"val_malli_{m}"]))
    for c, n in (("mus", "musta matta"), ("val", "valkoinen"), ("sin", "sininen"), ("vih", "vihreä")):
        bike_specs.append((f"Gravel, {n}", f"bike_gra_{c}", ["val_malli_gra", f"val_vari_{c}"]))
    _attr_images(env, _ref(env, "pt_polkupyora"), bike_specs)
    # Maalattu runko ja raakarunko: rungon kuva mallin mukaan. Värimaali: purkki sävyn mukaan.
    models_fi = (("gra", "Gravel"), ("maa", "Maasto"), ("man", "Maantie"), ("kau", "Kaupunki"), ("sah", "Sähkö"))
    for xid in ("pt_maalattu_runko", "pt_raakarunko"):
        _attr_images(env, _ref(env, xid), [(f"Runko, {n}", f"rr_{m}", [f"val_malli_{m}"]) for m, n in models_fi])
    _attr_images(env, _ref(env, "pt_varimaali"), [
        (n, f"ma_{c}", [f"val_vari_{c}"]) for c, n in (("pun", "Punainen"), ("mus", "Musta matta"), ("val", "Valkoinen"),
                                                       ("sin", "Sininen"), ("vih", "Vihreä"))])
    variants = (_ref(env, "pt_polkupyora") | _ref(env, "pt_maalattu_runko") | _ref(env, "pt_raakarunko")
                | _ref(env, "pt_varimaali")).with_context(active_test=False).product_variant_ids
    variants.filtered("variant_image_ids")._set_main_image_from_extra_images()


def post_init_hook(env):
    env = env(user=env.ref("base.user_admin").id, context=dict(env.context, lang="fi_FI", tracking_disable=True))
    sale_tax = _settings(env)
    _taxes_and_flags(env, sale_tax)
    _component_variants(env)
    _frames_plm(env)
    _boms(env)
    initial = {}
    from .tools_data import STOCK_PARTS
    initial.update(STOCK_PARTS)
    _stock(env, initial)
    _archive_valves(env)
    _demo_user(env)
    _images(env)
    _frame_families(env)
    _clear_stale_template_codes(env)
    _variant_code_prefixes(env)
    _ecr(env)
    _logger.info("rockit_bike_demo: alustus valmis")


def _clear_stale_template_codes(env):
    """Monivarianttisen tuotemallin koodi tyhjäksi (esim. [MA-VARI] Värimaali).

    Odoo tallentaa tuotemallin koodin ensimmäisen variantin koodista eikä tyhjennä sitä, kun malliin
    luodaan lisää (dynaamisia) variantteja. Koodi kuuluu varianteille (MA-MUS, MA-PUN, ...), joten
    vanhentunut mallikoodi näkyisi tuotteen, osaluettelorivien ja konfiguraattorin nimissä.
    Tyhjennys ei kirjoita variantteihin (Odoo kirjoittaa mallin koodin vain yksivarianttiselle).
    """
    xmlids = env["ir.model.data"].search([("module", "=", M), ("model", "=", "product.template")])
    templates = env["product.template"].browse(xmlids.mapped("res_id")).exists()
    templates |= env["product.template"].search([("engineering_code", "=like", "RR-%")])
    stale = templates.filtered(lambda t: t.active and t.default_code and len(t.product_variant_ids) > 1)
    if stale:
        _logger.info("rockit_bike_demo: tuotemallin koodi tyhjennetään: %s", stale.mapped("default_code"))
        stale.write({"default_code": False})
    return stale


# ---------------------------------------------------------------- varianttien tuotekoodit
CODE_PREFIXES = {"pt_polkupyora": "PP-", "pt_maalattu_runko": "MR-"}


def _variant_code_prefixes(env):
    """Konfiguroitavien tuotemallien varianteille luettavat koodit (PP-GRA-MUS-M-PER, MR-GRA-M-PUN).

    1. Ominaisuusarvoille koodi xmlid:n mukaan (val_malli_gra -> GRA), jos arvolla ei ole koodia tai
       sillä on product_variant_default_coden automaattinen kahden merkin koodi (nimen alku). Käsin
       annettu muu koodi jätetään ennalleen ja kirjataan lokiin.
    2. Variantit, joilla ei ole koodia, merkitään automaattisiksi (Manual Reference pois). Ne olivat
       käsin-tilassa vain siksi, että moduulin asennus merkitsi kaikki olemassa olevat variantit
       käsin annetuiksi. Variantit, joilla on koodi (raakarungot RR-*, värimaalit MA-*), eivät muutu.
    3. Tuotemallille koodin etuliite, ellei sitä ole; maski ja varianttien koodit lasketaan siitä.
    Toistettava.
    """
    Value, Product = env["product.attribute.value"], env["product.product"]
    for imd in env["ir.model.data"].search([("module", "=", M), ("model", "=", "product.attribute.value")]):
        value = Value.browse(imd.res_id).exists()
        target = imd.name.split("_", 2)[-1].upper()
        if not value or value.code == target:
            continue
        if value.code and value.code != (value.name or "")[:2]:
            _logger.info("rockit_bike_demo: arvon %s koodi %s on muokattu, ei muuteta", value.name, value.code)
            continue
        value.code = target
    templates = env["product.template"]
    for xid, prefix in CODE_PREFIXES.items():
        tmpl = env.ref(f"{M}.{xid}", raise_if_not_found=False)
        if not tmpl:
            continue
        templates |= tmpl
        uncoded = tmpl.with_context(active_test=False).product_variant_ids.filtered(lambda v: not v.default_code)
        if uncoded:
            uncoded.write({"manual_code": False})
        if not tmpl.code_prefix:
            tmpl.code_prefix = prefix
            tmpl.reference_mask = tmpl._get_default_mask()
        if uncoded:
            env.add_to_compute(Product._fields["default_code"], uncoded)
            uncoded.flush_recordset(["default_code"])
            _logger.info("rockit_bike_demo: %s variantille koodi: %s", tmpl.name, uncoded.mapped("default_code"))
    return templates


# ---------------------------------------------------------------- raakarungon malliperheet
MODEL_FI = {"MAA": "Maasto", "MAN": "Maantie", "GRA": "Gravel", "KAU": "Kaupunki", "SAH": "Sähkö"}
OLD_FRAME_NAME = "Raakarunko (vanha yhteinen tuotemalli)"


def _frame_family(env, m):
    """Mallin raakarunkoperhe RR-<malli>: ensimmäinen (alkuperäinen) aktiivinen revisio."""
    return env["product.template"].search([("engineering_code", "=", f"RR-{m}")], order="engineering_revision", limit=1)


def _frame_families(env):
    """Raakarunko jaetaan PLM-perheisiin mallin mukaan: RR-MAA, RR-MAN, RR-GRA, RR-KAU, RR-SAH.

    Perhe = suunnittelutaso (oma PLM-tunnus ja revisio, yksi piirustus per malli), variantti = logistiikkataso
    (koko, oma sisäinen koodi RR-<malli>-<koko>, saldo, täydennyssääntö, ostohinta). Vanhan yhteisen tuotemallin
    variantit saavat koodin ``…-VANHA`` ja arkistoidaan; saldot, täydennyssäännöt, toimittajahinnat, avoimet
    valmistustilausten rivit ja muutospyynnöt siirtyvät uusiin variantteihin. Maalatun rungon osaluettelorivin
    komponenttiperheiksi tulevat kaikki viisi perhettä. Ajon voi toistaa (tehdyt vaiheet ohitetaan).
    """
    PT = env["product.template"].with_context(active_test=False)
    if "engineering_code" not in PT._fields:
        return
    src = _ref(env, "pt_raakarunko").with_context(active_test=False)
    families = PT
    for m in MODELS:
        fam = _frame_family(env, m)
        if not fam:
            fam = _create_frame_family(env, src, m)
        families |= fam
        _frame_family_data(env, src, m)
    line = env["mrp.bom.line"]
    if "component_family_ids" in line._fields:
        bom = env.ref(f"{M}.bom_maalattu_runko", raise_if_not_found=False)
        frame_tmpls = src | families | PT.search([("engineering_code", "=like", "RR-%")])
        line = bom and bom.bom_line_ids.filtered(lambda l: l.component_template_id in frame_tmpls)[:1]
        if line and line.component_family_ids.ids != families.ids:
            line.write({"component_family_ids": [(6, 0, families.ids)]})
    if src.active and not src.product_variant_ids.filtered("active"):
        src.write({"name": OLD_FRAME_NAME})
        try:
            with env.cr.savepoint():
                src.write({"active": False})
        except Exception as e:  # pragma: no cover
            _logger.warning("Vanhan raakarunkomallin arkistointi epäonnistui: %s", e)
    # Tuotemallin tallennettu koodi jää muuten ensimmäisen variantin koodiksi (esim. [RR-MAA-S] perheen nimessä).
    stale = (src | families).filtered(lambda t: t.default_code and len(t.product_variant_ids) != 1)
    if stale:
        stale.write({"default_code": False})  # monivarianttisella mallilla ei kirjoita variantteihin
    return families


def _create_frame_family(env, src, m):
    from .tools_data import FRAME_COST
    malli, koko = _ref(env, "attr_malli"), _ref(env, "attr_koko")
    val = _ref(env, f"val_malli_{m.lower()}")
    sizes = env["product.attribute.value"].browse([_ref(env, f"val_koko_{s.lower()}").id for s in SIZES])
    vals = {
        "name": f"Raakarunko {MODEL_FI[m]}", "type": "consu", "is_storable": True, "engineering_code": f"RR-{m}",
        "engineering_material": FRAME_MATERIAL[m], "categ_id": src.categ_id.id, "uom_id": src.uom_id.id,
        "route_ids": [(6, 0, src.route_ids.ids)], "purchase_ok": True, "sale_ok": False, "list_price": 0,
        "description_purchase": f"Kuvitteellinen demonimike. Hitsattu {MODEL_FI[m].lower()}rungon raakarunko "
                                "ilman pintakäsittelyä, koko varianttina.",
        "taxes_id": [(6, 0, src.taxes_id.ids)], "supplier_taxes_id": [(6, 0, src.supplier_taxes_id.ids)],
        "attribute_line_ids": [(0, 0, {"attribute_id": malli.id, "value_ids": [(6, 0, val.ids)]}),
                               (0, 0, {"attribute_id": koko.id, "value_ids": [(6, 0, sizes.ids)]})],
    }
    if "auto_default_code" in src._fields:
        vals["auto_default_code"] = False
    t = env["product.template"].create(vals)
    wh = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
    stock = wh.lot_stock_id
    Quant = env["stock.quant"].with_context(inventory_mode=True)
    Orderpoint = env["stock.warehouse.orderpoint"].with_context(active_test=False)
    Activity = env["mail.activity"].with_context(active_test=False)
    old_variants = src.product_variant_ids.filtered(
        lambda p: p.active and val in p.product_template_attribute_value_ids.product_attribute_value_id)
    codes = {}
    for s in SIZES:
        size = _ref(env, f"val_koko_{s.lower()}")
        nv = t._create_product_variant(t.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id in (val | size)))
        ov = old_variants.filtered(lambda p: size in p.product_template_attribute_value_ids.product_attribute_value_id)[:1]
        code = f"RR-{m}-{s}"
        if ov and ov.default_code == code:
            ov.default_code = f"{code}-VANHA"
        nv_vals = {"default_code": code, "standard_price": ov.standard_price or FRAME_COST[m], "barcode": False}
        if "manual_code" in nv._fields:
            nv_vals["manual_code"] = True
        if ov:
            nv_vals.update({"weight": ov.weight, "volume": ov.volume})
            if ov.image_variant_1920:
                nv_vals["image_variant_1920"] = ov.image_variant_1920
        nv.write(nv_vals)
        codes[nv] = code
        if not ov:
            continue
        for seller in env["product.supplierinfo"].search([("product_id", "=", ov.id)]):
            seller.copy({"product_tmpl_id": t.id, "product_id": nv.id})
        for op in Orderpoint.search([("product_id", "=", ov.id), ("active", "=", True)]):
            op.copy({"product_id": nv.id})
            op.active = False
        if "linkeddocuments" in nv._fields and ov.linkeddocuments:
            nv.linkeddocuments = [(6, 0, ov.linkeddocuments.ids)]
        # avoimet valmistustilausten rivit: varaus pois, tuote vaihtuu, saldo siirtyy, varataan uudelleen
        moves = env["stock.move"].search([("product_id", "=", ov.id), ("state", "not in", ("done", "cancel"))])
        moves._do_unreserve()
        qty = ov.with_context(location=stock.id).qty_available
        if qty:
            Quant.create({"product_id": nv.id, "location_id": stock.id, "inventory_quantity": qty})._apply_inventory()
            for q in env["stock.quant"].search([("product_id", "=", ov.id), ("location_id", "child_of", stock.id)]):
                q.with_context(inventory_mode=True).write({"inventory_quantity": 0})
                q.with_context(inventory_mode=True).action_apply_inventory()
        moves.write({"product_id": nv.id})
        moves.raw_material_production_id.filtered(lambda p: p.state in ("confirmed", "progress")).action_assign()
        Activity.search([("res_model", "=", "product.product"), ("res_id", "=", ov.id)]).write({"res_id": nv.id})
        ov.active = False
    variant = t.product_variant_ids[:1]
    if variant.engineering_state == "draft":
        variant.action_confirm()
    if variant.engineering_state == "confirmed":
        variant.action_release()
    for nv, code in codes.items():  # PLM:n tilasiirtymä voi kirjoittaa koodin uudelleen
        if nv.default_code != code:
            nv.default_code = code
    _logger.info("rockit_bike_demo: raakarunkoperhe %s luotu (%s varianttia)", t.engineering_code, len(t.product_variant_ids))
    return t


def _frame_family_data(env, src, m):
    """Kuvat ja materiaali kaikille perheen revisioille (myös aiemmin ilman kuvia luodulle RR-GRA:lle)."""
    PT = env["product.template"]
    val = _ref(env, f"val_malli_{m.lower()}")
    image = src.product_template_image_ids.filtered(
        lambda i: val in i.attribute_value_ids.product_attribute_value_id)[:1] if "product_template_image_ids" in src._fields else False
    img = (image and image.image_1920) or _read_image(f"rr_{m.lower()}")
    old_variants = src.with_context(active_test=False).product_variant_ids
    for t in PT.search([("engineering_code", "=", f"RR-{m}")]):
        vals = {}
        if not t.engineering_material:
            vals["engineering_material"] = FRAME_MATERIAL[m]
        if not t.image_1920 and img:
            vals["image_1920"] = img
        if vals:
            t.write(vals)
        if "product_template_image_ids" in t._fields and not t.product_template_image_ids and img:
            env["product.image"].with_context(skip_update_main_image=True).create({
                "name": f"Runko, {MODEL_FI[m]}", "sequence": 1, "image_1920": img, "product_tmpl_id": t.id,
                "attribute_value_ids": [(6, 0, t.attribute_line_ids.filtered(
                    lambda l: l.attribute_id == _ref(env, "attr_malli")).product_template_value_ids.ids)]})
        for nv in t.product_variant_ids.filtered(lambda p: not p.image_variant_1920):
            ov = old_variants.filtered(lambda p: p.default_code == f"{nv.default_code}-VANHA" and p.image_variant_1920)[:1]
            if ov or img:
                nv.image_variant_1920 = ov.image_variant_1920 if ov else img
