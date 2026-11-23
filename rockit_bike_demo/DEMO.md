# Polkupyörädemo – demokäsikirjoitus

Tilausohjautuva polkupyörä alusta loppuun: verkkokauppa → myynti → ostot → vastaanotto →
maalaamo → kokoonpano → toimitus → laskut → vienti taloushallintoon. Lisäksi PLM-muutospyyntö
raakarungolle. Kaikki yritykset, nimikkeet ja hinnat ovat **kuvitteellista demodataa**.

Julkinen sivusto ja verkkokauppa: https://plm.rockit.fi (kuvitteellinen *Pyöräpaja Demo Oy*).
Taustajärjestelmä: https://plm.rockit.fi/web/login (ylläpitäjän omilla tunnuksilla; julkista demokirjautumista ei ole).
Kesto: noin 20–30 min.

## Valmiina demossa

| Tilanne | Tilaus | Mitä näyttää |
|---|---|---|
| Valmis esimerkki | S00002 Gravel, Punainen, M, Premium (verkkokaupasta) | Koko ketju tehty: P00001, WH/MO/00002 (runko), WH/MO/00001 (pyörä), toimitus, asiakaslasku ja toimittajan lasku |
| Valmis esimerkki (BOM v2) | S00011 Gravel, Punainen, M, Premium | Koko ketju tehty uudella rakenteella: P00007, WH/MO/00014 (maalattu runko), WH/MO/00013 (pyörä), toimitus ja laskut |
| Avoin, ostot kesken | S00012 Sähkö, Sininen, L, Perus + valosarja | Valmistustilaukset WH/MO/00015 (pyörä) ja WH/MO/00016 (runko) odottavat, ostoehdotus P00008 (E-Veto Demo Oy: moottori, akku, näyttö) vahvistamatta |
| PLM | ECR-0101 Gravel-rungon geometria (RR-GRA-M) | Avoin muutospyyntö (tila *in_progress*, ei vielä ECO:a), josta tehdään esityksessä muutosmääräys ECO-0001 ja rungon revisio 1 (luku 8) |
| PLM | Polkupyörän osaluettelo *PP / B* | Osaluetteloversio 2 aktiivinen, versio 1 (*PP / A*) historiallinen |

## 1. Asiakas konfiguroi pyörän (verkkokauppa)
1. Avaa `https://plm.rockit.fi/shop` → **Polkupyörä**.
2. Valitse **Malli** (Maasto, Maantie, Gravel, Kaupunki, Sähkö), **Väri**, **Koko** ja **Vaihteisto**.
   Hinta päivittyy valintojen mukaan (sis. ALV 25,5 %). Esim. Kaupunki/Perus 1 190 €, Sähkö +1 900 €, Premium +490 €.
3. **Lisää ostoskoriin** → ikkunassa tarjotaan lisävarusteet (lokasuojat, teline, valot, lukko).
4. **Kassa** → osoite → maksutapa **Tilisiirto** → tilaus syntyy tarjouksena. Kauppa on demo: tilauksia ei toimiteta eikä laskuteta oikeasti.

Huom: variantti luodaan vasta tilattaessa (dynaaminen variantti), joten 200 yhdistelmää ei kuormita tuotelistaa.
Sama koskee maalattua runkoa: sen variantti (malli × koko × väri) luodaan, kun pyörän BOM räjäytetään.

## 2. Myyjä vahvistaa tilauksen
**Myynti → Tilaukset → Tarjoukset** → avaa verkkotilaus → **Vahvista**.
Vahvistus käynnistää tilausohjautuvan ketjun (MTO):
- pyörälle valmistustilaus (BOM *PP / B*), joka valitsee komponentit konfiguraation mukaan
- maalatulle rungolle oma valmistustilaus (BOM *MR / B*): oikea raakarunko (malli × koko) ja oikea värimaali
- tilausohjautuvista osista (Premium-voimansiirto, sähkömoottori, akku, näyttö) ostoehdotus toimittajalle
- varastonimikkeet otetaan varastosta; täydennyssäännöt (min/max) tekevät ostoehdotuksen, kun saldo alittaa minimin

Näytä myyntitilauksen pikapainikkeet: *Valmistus* ja *Ostot*.

## 3. Ostot ja vastaanotto
1. **Ostot → Tilaukset** → avaa ostoehdotus (esim. P00008) → toimittaja, hinta ja toimitusaika tulevat toimittajahinnastosta → **Vahvista tilaus**.
2. **Vastaanota tuotteet** → **Vahvista**.
3. Näytä **Varasto → Raportointi → Täydennys**: varastonimikkeiden min/max-säännöt.

## 4. Maalaamo: maalattu runko
**Valmistus → Valmistustilaukset** → *Maalattu runko (malli, koko, väri)*.
- Komponentit: raakarunko (PLM-nimike, esim. RR-GRA-M), pohjamaali 0,3 l, värimaali 0,4 l, kirkaslakka 0,3 l.
- Työvaiheet: Esikäsittely (pesu ja hionta) → Maalaamo: pohjamaalaus, värimaalaus ja lakkaus, kuivaus uunissa 45 min.
- Työohje näkyy valmistustilauksen huomautuksissa.
- **Tarkista saatavuus** → **Valmis** (tai työvaiheet yksitellen *Työtilaukset*-välilehdeltä).

## 5. Kokoonpano, säätö ja pakkaus
Avaa pyörän valmistustilaus. Maalattu runko on nyt saatavilla.
- Työvaiheet: Kokoonpano 75 min, (Sähkö: Sähkövetojärjestelmän asennus 30 min), Säätö ja laadunvarmistus 25 min, Pakkaus 15 min.
- Laadunvarmistuksen tarkistuslista on valmistustilauksen huomautuksissa (Odoo CE:ssä ei ole Laatu-moduulia).
- **Valmis**.

## 6. Toimitus asiakkaalle
Myyntitilaus → **Toimitus** → **Vahvista**.

## 7. Laskut ja vienti taloushallintoon
1. Myyntitilaus → **Luo lasku** → **Vahvista** (asiakaslasku, ALV 25,5 % sisältyy hintaan).
2. Ostotilaus → **Luo lasku** → laskupäivä ja toimittajan laskunumero → **Vahvista**.
3. **Laskutus → Asiakkaat → Laskut** (tai Toimittajat → Laskut) → valitse rivit → **Toiminnot → Vie** →
   valitse tallennettu vientipohja **Taloushallintoon** (laskut) tai **Taloushallintoon (rivit)** (kirjausrivit tileineen) → CSV.
   Tämä kuvaa liittymää ulkoiseen kirjanpitoon; maksut ja kirjanpito hoidetaan siellä.

## 8. PLM: muutospyyntö ja muutosmääräys (ECR-0101 → ECO)
odooplm:n painikkeet ovat englanniksi.

**Valmistelu (valinnainen, tekee vaikutusanalyysistä näyttävämmän):** tilaa verkkokaupasta Gravel, M
(mikä tahansa väri) ja vahvista tilaus → maalatun rungon valmistustilaus varaa `RR-GRA-M` rev 0:n.

1. **PLM → Components** → *Raakarunko Gravel* (`RR-GRA`, rev 0, *released*). Näytä:
   - sisäinen koodi `RR-GRA-M` ilman revisiota, *Rev.*-sarake; varianteilla toimittajahinta (170 €, 21 pv) ja min/max-säännöt
   - maalatun rungon osaluettelo *MR / B*: yksi rivi, *Komponenttiperheet* `RR-MAA`, `RR-MAN`, `RR-GRA`, `RR-KAU`, `RR-SAH`, kelluva revisio
   - *PLM → Components* on ryhmitelty nimikekoodin (perheen) mukaan; sarakkeet *Tuotekoodi* ja *Varianttiarvot* erottavat koot
2. Toimenpide **ECR-0101 Gravel-rungon geometria** (tila *in_progress*) → painike **ECO**.
   Syntyy **ECO-0001** (*PLM → Muutosmääräykset (ECO)*, myös *Avaa ECO*); ECR:n tila *eco*.
3. ECO:ssa: muutettava nimike *Raakarunko Gravel* rev 0 (valmiina). *Voimaantulo*: **Käytä ensin vanha varasto**
   (kerro myös *Heti* ja *Päivästä alkaen*). **Analysoi vaikutukset** → *Vaikutukset*-välilehti:
   käyttökohde (maalatun rungon osaluettelo, kelluva), varasto rev 0 (S 3, M 2, L 3, XL 3), avoimet valmistus- ja ostotilaukset.
4. **Luo revisiot** → rev 1 luonnoksena: samat koodit, toimittajahinnat, asiakirja, osaluettelot siirtyivät.
   Muokkaa rev 1:n toimittajahinta esim. 178 € / 28 pv.
5. Rev 1: **Confirm** → **Release**. ECO sulkeutuu (*Vapautettu*), ECR valmis, rev 0 *obsoleted* (käytä ensin).
   Viestiketjussa yhteenveto ja avointen tilausten määrä.
6. ECO → **Avoimet tilaukset**: aloittamattomat valmistustilaukset ja tarjouspyynnöt siirretään rev 1:een
   (vanha varasto jää rev 0:lle), vahvistetut ostot vain listataan → **Päivitä valitut**.
7. **Varasto → Täydennys**: rev 1:n säännöllä sarake *Korvatun revision varasto* – uutta tilataan vain siltä osin kuin vanha ei riitä.
8. Uusi valmistustilaus Gravel-rungolle: komponenttirivi jakautuu esim. *rev 0 (varastosta) + rev 1*.
9. (Valinnainen) Osaluetteloversio: uusi ECO → *Osaluetteloversiot*-välilehdelle *PP / B* → voimaantulo *Heti* →
   **Luo revisiot** → lisää luonnosversioon rivi → **Sulje ECO** → versio 3 aktiivinen, versio 2 historiallinen.

Esitys muuttaa kantaa (ECO, revisio, tilaukset): ota varmuuskopio ennen esitystä ja palauta se esityksen jälkeen.

## Rakenne lyhyesti
- **Polkupyörä** (myytävä, dynaamiset variantit: Malli × Väri × Koko × Vaihteisto = 200 yhdistelmää), reitti MTO + Valmista
  - **Maalattu runko** (alikokoonpano, samat ominaisuudet Malli × Koko × Väri, dynaamiset variantit), reitti MTO + Valmista
    - Raakarunko: viisi PLM-tuotemallia (komponenttiperheet), yksi per malli: *Raakarunko Maasto* `RR-MAA`,
      *Maantie* `RR-MAN`, *Gravel* `RR-GRA`, *Kaupunki* `RR-KAU`, *Sähkö* `RR-SAH`; kullakin 4 kokoa (RR-GRA-M jne.),
      kuva, materiaali, varastoon, min/max-säännöt 1/4
    - Värimaali (tuotemalli, 5 väriä, MA-PUN jne.), pohjamaali ja kirkaslakka litroina, varastoon
  - Haarukka (Gravel-haarukka `HA-GRA` on PLM-nimike), kiekkosarja, renkaat mallin mukaan; voimansiirto Perus/Premium; vanne- tai levyjarrut; drop- tai suora ohjaamo;
    satula, satulatolppa, polkimet; sähkömallissa moottori, akku ja näyttö; vaijerit, pultit, pakkauslaatikko
- Ostot: MTO + Osta = Premium-voimansiirto ja sähköosat; muut varastoon min/max-säännöillä
- Toimittajat (kuvitteellisia): Runkopaja Demo Oy, Komponenttitukku Demo Oy, Kiekko ja Rengas Demo Oy, E-Veto Demo Oy,
  Maalitukku Demo Oy, Pienosa Demo Oy
- Työpisteet: Esikäsittely, Maalaamo, Kokoonpano, Säätö ja laadunvarmistus, Pakkaus

## BOM-rakenne (v2, OCA mrp_bom_attribute_match)
Variantit saavat tuotekoodin ominaisuusarvojen koodeista: Polkupyörä esimerkiksi *PP-GRA-MUS-M-PER*
(etuliite PP-, malli, väri, koko, vaihteisto) ja Maalattu runko *MR-GRA-PUN-M* (etuliite MR-, malli, väri, koko).
Raakarunkojen (RR-*) ja värimaalien (MA-*) koodit on annettu käsin, eivätkä ne muutu.

Pyörän BOM *PP / B* on lyhyt: yksi tuotemallirivi *Maalattu runko*, jonka variantti valitaan pyörän
ominaisuuksista Malli, Koko ja Väri, sekä mallikohtaiset osat (*Käytä varianteille*). Maalatun rungon BOM
*MR / B* sisältää tuotemallirivit *Raakarunko* (Malli + Koko) ja *Värimaali* (Väri) sekä pohjamaalin ja lakan.
Moduulit: `mrp_bom_attribute_match` (OCA, ks. `VENDORED.md`) ja RockIT-laajennus
`rockit_bom_attribute_match_dynamic` (dynaamisten varianttien luonti, BOM-kustannus, rakenneraportti,
kulutusvaroitus). Vanhat v1-nimikkeet ja -BOMit (100 maalattua runkoa, 130 riviä) on arkistoitu;
valmis esimerkki S00002 on tehty v1-rakenteella.

## PLM-revisiot (22.11.2026 alkaen)
Moduulit `rockit_plm_floating_revision`, `rockit_plm_eco`, `rockit_mrp_bom_component_family`,
`rockit_plm_variant_default_code`, `rockit_plm_breakages_access` sekä OCA `mrp_bom_version` ja
`product_variant_default_code`; odooplm:n `plm_date_bom` poistettu. Gravel-rungot siirrettiin omaksi
PLM-perheekseen `RR-GRA` (vanhat Gravel-variantit arkistoitu koodilla `…-VANHA`), ECR-0101 osoittaa uuteen
`RR-GRA-M`:ään.

Samana päivänä myös *Raakarunko (muut mallit)* jaettiin perheisiin `RR-MAA`, `RR-MAN`, `RR-KAU` ja `RR-SAH`
(rockit_bike_demo 20.0.2.1.0, `hooks._frame_families`): koodit `RR-<MALLI>-<KOKO>` ennallaan, saldot,
täydennyssäännöt, toimittajahinnat ja kuvat siirretty, vanhat variantit arkistoitu koodilla `…-VANHA` ja
vanha tuotemalli nimellä *Raakarunko (vanha yhteinen tuotemalli)*. Uusi revisio saa nyt myös kuvat ja
materiaalitiedot (rockit_plm_floating_revision 20.0.1.3.0).
