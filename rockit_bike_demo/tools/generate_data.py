# Copyright 2026 RockIT Oy
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Generoi rockit_bike_demo/data/*.xml. Aja: python3 tools/generate_data.py
Kaikki nimet, hinnat ja toimittajat ovat kuvitteellista demodataa."""
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

OUT = Path(__file__).resolve().parent.parent / "data"

MODELS = [("MAA", "Maasto"), ("MAN", "Maantie"), ("GRA", "Gravel"), ("KAU", "Kaupunki"), ("SAH", "Sähkö")]
# Hinnat sis. ALV 25,5 % (kuluttajahinta verkkokaupassa); lisähinta kaupunkimallin päälle
MODEL_EXTRA = {"MAA": 900, "MAN": 1000, "GRA": 800, "KAU": 0, "SAH": 1900}
COLORS = [("MUS", "Musta matta", "#2b2b2b"), ("VAL", "Valkoinen", "#f4f4f2"), ("PUN", "Punainen", "#c62828"),
          ("SIN", "Sininen", "#1e5aa8"), ("VIH", "Vihreä", "#2e7d32")]
SIZES = [("S", "S (155–165 cm)"), ("M", "M (165–175 cm)"), ("L", "L (175–185 cm)"), ("XL", "XL (185–195 cm)")]
GEARS = [("PER", "Perus (1×10)", 0), ("PRE", "Premium (1×12)", 490)]

VENDORS = [
    # key, name, city, country, ref, role
    ("runko", "Runkopaja Demo Oy", "Lahti", "fi", "DEMO-P01", "Raakarungot (alumiini ja teräs)"),
    ("komp", "Komponenttitukku Demo Oy", "Vantaa", "fi", "DEMO-P02", "Voimansiirto, jarrut, ohjaamo, satulat, haarukat ja lisävarusteet"),
    ("kiekko", "Kiekko ja Rengas Demo Oy", "Jyväskylä", "fi", "DEMO-P03", "Kiekkosarjat ja renkaat"),
    ("eveto", "E-Veto Demo Oy", "Espoo", "fi", "DEMO-P04", "Sähköpyörän moottorit, akut ja näytöt"),
    ("maali", "Maalitukku Demo Oy", "Tampere", "fi", "DEMO-P05", "Pohjamaalit, värimaalit ja lakat"),
    ("pien", "Pienosa Demo Oy", "Oulu", "fi", "DEMO-P06", "Vaijerit, kiinnikkeet ja pakkausmateriaalit"),
]

# code, name, categ, vendor, cost (ALV 0), lead days, uom, procurement ('stock' | 'mto'), [min, max, initial]
FRAME_COST = {"MAA": 180, "MAN": 190, "GRA": 170, "KAU": 120, "SAH": 210}
# Raakarunko (Malli × Koko) ja värimaali (Väri) ovat variantillisia tuotemalleja: ks. VARIANT_PARTS ja hooks.py
FRAME_STOCK = (1, 4, 3)
PAINT_STOCK = (2, 8, 6)
PARTS = [
    ("MA-POHJA", "Pohjamaali (epoksi)", "paint", "maali", 28, 5, "litre", "stock", (2, 10, 8)),
    ("MA-LAKKA", "Kirkaslakka (2K)", "paint", "maali", 38, 5, "litre", "stock", (2, 10, 8)),
]
FORKS = {"MAA": ("Joustohaarukka 29\" 120 mm", 240), "MAN": ("Hiilikuituhaarukka maantie", 160),
         "GRA": ("Hiilikuituhaarukka gravel", 150), "KAU": ("Teräshaarukka kaupunki 28\"", 35),
         "SAH": ("Joustohaarukka 27,5\" 100 mm (e-bike)", 180)}
WHEELS = {"MAA": ("Kiekkosarja 29\" Boost", 190, "kiekko"), "MAN": ("Kiekkosarja 700c maantie", 220, "kiekko"),
          "GRA": ("Kiekkosarja 700c gravel", 200, "kiekko"), "KAU": ("Kiekkosarja 28\" kaupunki", 90, "kiekko"),
          "SAH": ("Kiekkosarja 27,5\" vahvistettu (e-bike)", 160, "kiekko")}
TYRES = {"MAA": ("Renkaat 29×2,4 (pari)", 60), "MAN": ("Renkaat 700×28 (pari)", 50), "GRA": ("Renkaat 700×40 (pari)", 55),
         "KAU": ("Renkaat 28×1,6 heijastinraidalla (pari)", 30), "SAH": ("Renkaat 27,5×2,6 E-rated (pari)", 65)}
for mk, _mn in MODELS:
    PARTS.append((f"HA-{mk}", FORKS[mk][0], "comp", "komp", FORKS[mk][1], 7, "unit", "stock", (1, 4, 3)))
    PARTS.append((f"KS-{mk}", WHEELS[mk][0], "comp", "kiekko", WHEELS[mk][1], 7, "unit", "stock", (1, 4, 3)))
    PARTS.append((f"RE-{mk}", TYRES[mk][0], "comp", "kiekko", TYRES[mk][1], 7, "unit", "stock", (1, 4, 3)))
PARTS += [
    ("VS-PER", "Voimansiirtosarja Perus 1×10", "comp", "komp", 140, 7, "unit", "stock", (2, 6, 5)),
    ("VS-PRE", "Voimansiirtosarja Premium 1×12", "comp", "komp", 420, 5, "unit", "mto", None),
    ("JA-VAN", "Vannejarrusarja", "comp", "komp", 30, 7, "unit", "stock", (1, 4, 3)),
    ("JA-LEV", "Hydraulinen levyjarrusarja", "comp", "komp", 120, 7, "unit", "stock", (2, 6, 5)),
    ("OH-DROP", "Ohjaamosarja, drop-tanko + stemmi", "comp", "komp", 70, 7, "unit", "stock", (1, 4, 3)),
    ("OH-SUO", "Ohjaamosarja, suora tanko + stemmi", "comp", "komp", 45, 7, "unit", "stock", (2, 6, 5)),
    ("SA-SAT", "Satula", "comp", "komp", 25, 7, "unit", "stock", (2, 8, 6)),
    ("SA-TOL", "Satulatolppa 31,6 mm", "comp", "komp", 18, 7, "unit", "stock", (2, 8, 6)),
    ("PO-ALU", "Polkimet, alumiini", "comp", "komp", 15, 7, "unit", "stock", (2, 8, 6)),
    ("EV-MOOT", "Keskimoottori 250 W", "ebike", "eveto", 520, 10, "unit", "mto", None),
    ("EV-AKKU", "Akku 500 Wh", "ebike", "eveto", 380, 10, "unit", "mto", None),
    ("EV-NAYT", "Näyttö ja ohjausyksikkö", "ebike", "eveto", 85, 10, "unit", "mto", None),
    ("PI-VAIJ", "Vaijeri- ja kuorisarja", "small", "pien", 6, 3, "unit", "stock", (5, 20, 15)),
    ("PI-PULT", "Pultti- ja kiinnikesarja", "small", "pien", 4, 3, "unit", "stock", (5, 20, 15)),
    ("PI-LAAT", "Pyörän pakkauslaatikko", "small", "pien", 8, 3, "unit", "stock", (5, 20, 15)),
]
# code, name, cost, sale price incl. VAT, vendor, description
ACCESSORIES = [
    ("LV-LOKA", "Lokasuojasarja", 15, 49, "komp", "Etu- ja takalokasuoja, sopii kaikkiin malleihin."),
    ("LV-TELI", "Tavarateline", 20, 59, "komp", "Alumiininen takateline, kantavuus 25 kg."),
    ("LV-VALO", "Valosarja (LED etu + taka)", 14, 39, "komp", "USB-ladattava valosarja."),
    ("LV-LUKKO", "U-lukko", 16, 45, "komp", "Karkaistu U-lukko kiinnikkeellä."),
]
CATEGS = [("root", "Polkupyörädemo", None), ("sale", "Myytävät pyörät", "root"), ("acc", "Lisävarusteet", "root"),
          ("sub", "Alikokoonpanot", "root"), ("frame", "Raakarungot", "root"), ("comp", "Komponentit", "root"),
          ("ebike", "Sähkövetojärjestelmä", "root"), ("paint", "Maalit ja pintakäsittely", "root"),
          ("small", "Pienosat ja pakkaus", "root")]
WORKCENTERS = [
    ("esik", "Esikäsittely", "ESIK", 45, "Rungon pesu, rasvanpoisto ja hionta ennen maalausta."),
    ("maal", "Maalaamo", "MAAL", 55, "Maalauskoppi ja kuivausuuni: pohjamaali, värimaali, lakka ja kuivaus."),
    ("koko", "Kokoonpano", "KOKO", 50, "Pyörän kokoonpano maalatusta rungosta ja ostetuista osista."),
    ("saato", "Säätö ja laadunvarmistus", "SQA", 50, "Vaihteiden ja jarrujen säätö, tarkistuslista ja koeajo."),
    ("pakk", "Pakkaus", "PAKK", 40, "Pakkaus kuljetuslaatikkoon ja lähetyksen valmistelu."),
]


def rec(xid, model, fields):
    out = [f'        <record id="{xid}" model="{model}">']
    for k, v in fields:
        if isinstance(v, tuple) and v[0] == "ref":
            out.append(f'            <field name="{k}" ref="{v[1]}"/>')
        elif isinstance(v, tuple) and v[0] == "eval":
            out.append(f'            <field name="{k}" eval={quoteattr(v[1])}/>')
        elif isinstance(v, bool):
            out.append(f'            <field name="{k}" eval="{v}"/>')
        elif isinstance(v, (int, float)):
            out.append(f'            <field name="{k}" eval="{v}"/>')
        else:
            out.append(f'            <field name="{k}">{escape(str(v))}</field>')
    out.append("        </record>")
    return "\n".join(out)


def write(name, records, header):
    body = "\n\n".join(records)
    (OUT / name).write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<!-- {header} (generoitu: tools/generate_data.py) -->\n'
                            f'<odoo>\n    <data noupdate="1">\n{body}\n    </data>\n</odoo>\n', encoding="utf-8")


def xid(code):
    return "pt_" + code.lower().replace("-", "_")


def main():
    OUT.mkdir(exist_ok=True)
    # --- partners, categories, workcenters
    r = []
    for key, name, city, cc, ref, role in VENDORS:
        r.append(rec(f"vendor_{key}", "res.partner", [
            ("name", name), ("is_company", True), ("city", city), ("country_id", ("ref", f"base.{cc}")), ("ref", ref),
            ("supplier_rank", 1),
            ("comment", f"<p>KUVITTEELLINEN DEMOTOIMITTAJA (polkupyörädemo). Ei oikea yritys. Toimittaa: {role}.</p>")]))
    r.append(rec("customer_demo", "res.partner", [
        ("name", "Aino Asiakas (demo)"), ("street", "Esimerkkikatu 1"), ("zip", "33100"), ("city", "Tampere"),
        ("country_id", ("ref", "base.fi")), ("email", "aino.asiakas@example.com"), ("customer_rank", 1),
        ("comment", "<p>Kuvitteellinen demoasiakas.</p>")]))
    r.append(rec("customer_demo2", "res.partner", [
        ("name", "Pekka Pyöräilijä (demo)"), ("street", "Esimerkkikatu 5"), ("zip", "40100"), ("city", "Jyväskylä"),
        ("country_id", ("ref", "base.fi")), ("email", "pekka.pyorailija@example.com"), ("customer_rank", 1),
        ("comment", "<p>Kuvitteellinen demoasiakas.</p>")]))
    for key, name, parent in CATEGS:
        f = [("name", name)]
        if parent:
            f.append(("parent_id", ("ref", f"categ_{parent}")))
        r.append(rec(f"categ_{key}", "product.category", f))
    for key, name, code, cost, note in WORKCENTERS:
        r.append(rec(f"wc_{key}", "mrp.workcenter", [("name", name), ("code", code), ("costs_hour", cost),
                                                      ("time_start", 5 if key in ("maal", "esik") else 0), ("note", f"<p>{note}</p>")]))
    r.append(rec("pubcat_bikes", "product.public.category", [("name", "Polkupyörät"), ("sequence", 1)]))
    r.append(rec("pubcat_acc", "product.public.category", [("name", "Lisävarusteet"), ("sequence", 2)]))
    write("base_data.xml", r, "Toimittajat, demoasiakkaat, tuoteryhmät ja työpisteet")

    # --- attributes
    r = []
    def attr(key, name, mode, display, values, seq):
        r.append(rec(f"attr_{key}", "product.attribute", [("name", name), ("create_variant", mode), ("display_type", display), ("sequence", seq)]))
        for i, v in enumerate(values):
            # code: product_variant_default_code builds variant references from these (PP-GRA-MUS-M-PER)
            f = [("name", v[1]), ("attribute_id", ("ref", f"attr_{key}")), ("sequence", i + 1), ("code", v[0])]
            if len(v) > 2 and v[2]:
                f.append(v[2])
            r.append(rec(f"val_{key}_{v[0].lower()}", "product.attribute.value", f))
    attr("malli", "Malli", "dynamic", "radio", [(k, n, ("default_extra_price", MODEL_EXTRA[k])) for k, n in MODELS], 1)
    attr("vari", "Väri", "dynamic", "color", [(k, n, ("html_color", h)) for k, n, h in COLORS], 2)
    attr("koko", "Koko", "dynamic", "pills", [(k, n) for k, n in SIZES], 3)
    attr("vaiht", "Vaihteisto", "dynamic", "radio", [(k, n, ("default_extra_price", e)) for k, n, e in GEARS], 4)
    write("attributes.xml", r, "Konfiguraattorin ominaisuudet")

    # --- products
    r = []
    uom = {"unit": "uom.product_uom_unit", "litre": "uom.product_uom_litre"}
    for code, name, categ, vendor, cost, lead, u, proc, stock in PARTS:
        # Odoo 20: Osta/Valmista ovat varaston reittejä (toimittaja -> Osta, BOM -> Valmista); tuotteelle vain MTO
        routes = "[(6, 0, [ref('stock.route_warehouse0_mto')])]" if proc == "mto" else "[(5, 0, 0)]"
        f = [("name", name), ("default_code", code), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", f"categ_{categ}")),
             ("uom_id", ("ref", uom[u])), ("standard_price", cost), ("list_price", 0), ("sale_ok", False), ("purchase_ok", True),
             ("route_ids", ("eval", routes)),
             ("description_purchase", "Kuvitteellinen demonimike." + (" Tilausohjautuva osto (MTO + Osta)." if proc == "mto" else ""))]
        r.append(rec(xid(code), "product.template", f))
        r.append(rec(xid(code) + "_seller", "product.supplierinfo", [
            ("partner_id", ("ref", f"vendor_{vendor}")), ("product_tmpl_id", ("ref", xid(code))), ("price", cost),
            ("delay", lead), ("min_qty", 1)]))
    for code, name, cost, price, vendor, desc in ACCESSORIES:
        r.append(rec(xid(code), "product.template", [
            ("name", name), ("default_code", code), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", "categ_acc")),
            ("standard_price", cost), ("list_price", price), ("sale_ok", True), ("purchase_ok", True),
            ("allow_out_of_stock_order", True), ("is_published", True),
            ("public_categ_ids", ("eval", "[(6, 0, [ref('pubcat_acc')])]")),
            ("description_sale", desc), ("description_ecommerce", f"<p>{desc}</p>")]))
        r.append(rec(xid(code) + "_seller", "product.supplierinfo", [
            ("partner_id", ("ref", f"vendor_{vendor}")), ("product_tmpl_id", ("ref", xid(code))), ("price", cost), ("delay", 7), ("min_qty", 1)]))
    mfg = "[(6, 0, [ref('stock.route_warehouse0_mto')])]"
    vals = lambda key, items: f"[(6, 0, [{', '.join(f'ref({chr(39)}val_{key}_{k.lower()}{chr(39)})' for k in items)}])]"
    attr_lines = lambda spec: ("eval", "[" + ", ".join(
        f"(0, 0, {{'attribute_id': ref('attr_{a}'), 'value_ids': {vals(a, ks)}}})" for a, ks in spec) + "]")
    ALL = {"malli": [k for k, _ in MODELS], "koko": [k for k, _ in SIZES], "vari": [k for k, _, _ in COLORS]}
    # Raakarunko: Malli × Koko (20 varianttia, luodaan hookissa; hinnat ja toimittajahinnat varianteittain)
    r.append(rec("pt_raakarunko", "product.template", [
        ("name", "Raakarunko"), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", "categ_frame")),
        ("uom_id", ("ref", uom["unit"])), ("list_price", 0), ("sale_ok", False), ("purchase_ok", True), ("route_ids", ("eval", "[(5, 0, 0)]")),
        ("description_purchase", "Kuvitteellinen demonimike. Hitsattu raakarunko ilman pintakäsittelyä, malli ja koko varianttina."),
        ("attribute_line_ids", attr_lines((("malli", ALL["malli"]), ("koko", ALL["koko"]))))]))
    # Värimaali: Väri (5 varianttia)
    r.append(rec("pt_varimaali", "product.template", [
        ("name", "Värimaali"), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", "categ_paint")),
        ("uom_id", ("ref", uom["litre"])), ("standard_price", 45), ("list_price", 0), ("sale_ok", False), ("purchase_ok", True),
        ("route_ids", ("eval", "[(5, 0, 0)]")), ("description_purchase", "Kuvitteellinen demonimike. Sävy varianttina."),
        ("attribute_line_ids", attr_lines((("vari", ALL["vari"]),)))]))
    r.append(rec("pt_varimaali_seller", "product.supplierinfo", [
        ("partner_id", ("ref", "vendor_maali")), ("product_tmpl_id", ("ref", "pt_varimaali")), ("price", 45), ("delay", 5), ("min_qty", 1)]))
    # Maalattu runko: samat ominaisuudet kuin pyörällä (Malli, Koko, Väri) -> BOM-rivit täsmäävät ominaisuuksien perusteella
    r.append(rec("pt_maalattu_runko", "product.template", [
        ("name", "Maalattu runko"), ("code_prefix", "MR-"), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", "categ_sub")),
        ("sale_ok", False), ("purchase_ok", False), ("route_ids", ("eval", mfg)),
        ("description", "<p>Alikokoonpano: raakarunko esikäsitellään ja maalataan omassa maalaamossa asiakkaan valitsemalla värillä.</p>"),
        ("attribute_line_ids", attr_lines((("malli", ALL["malli"]), ("koko", ALL["koko"]), ("vari", ALL["vari"]))))]))
    r.append(rec("pt_polkupyora", "product.template", [
        ("name", "Polkupyörä"), ("code_prefix", "PP-"), ("type", "consu"), ("is_storable", True), ("categ_id", ("ref", "categ_sale")),
        ("list_price", 1190), ("sale_ok", True), ("purchase_ok", False), ("route_ids", ("eval", mfg)),
        ("allow_out_of_stock_order", True), ("is_published", True), ("public_categ_ids", ("eval", "[(6, 0, [ref('pubcat_bikes')])]")),
        ("sale_delay", 14),
        ("description_sale", "Tilauksesta koottava polkupyörä. Runko maalataan valitsemallasi värillä."),
        ("description_ecommerce", "<p><b>Rakenna oma pyöräsi.</b> Valitse malli, väri, koko ja vaihteisto. Maalaamme rungon "
         "ja kokoamme pyörän tilauksesi mukaan omalla tehtaallamme Tampereella. Toimitusaika noin 2 viikkoa.</p>"
         "<p><i>Tämä on AvoinPLM-demon kuvitteellinen tuote. Tilauksia ei toimiteta eikä laskuteta.</i></p>"),
        ("optional_product_ids", ("eval", "[(6, 0, [" + ", ".join(f"ref('{xid(a[0])}')" for a in ACCESSORIES) + "])]")),
        ("accessory_product_ids", ("eval", "[(6, 0, [])]")),
        ("attribute_line_ids", ("eval", "[" + ", ".join(
            f"(0, 0, {{'attribute_id': ref('attr_{a}'), 'value_ids': {vals(a, ks)}}})" for a, ks in
            (("malli", [k for k, _ in MODELS]), ("vari", [k for k, _, _ in COLORS]), ("koko", [k for k, _ in SIZES]),
             ("vaiht", [k for k, _, _ in GEARS]))) + "]"))]))
    write("products.xml", r, "Nimikkeet, toimittajahinnat ja myytävät tuotteet")
    stock = {c: st for c, _n, _cat, _v, _co, _l, _u, proc, st in PARTS if proc == "stock"}
    stock.update({f"RR-{m}-{sz}": FRAME_STOCK for m, _ in MODELS for sz, _ in SIZES})
    stock.update({f"MA-{c}": PAINT_STOCK for c, _, _ in COLORS})
    stock.update({a[0]: (2, 8, 5) for a in ACCESSORIES})
    (OUT.parent / "tools_data.py").write_text(
        "# Copyright 2026 RockIT Oy\n# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).\n"
        '"""Generoitu: tools/generate_data.py. Varastoitavat nimikkeet: koodi -> (min, max, alkusaldo)."""\n'
        f"STOCK_PARTS = {stock!r}\nFRAME_COST = {FRAME_COST!r}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
