**Status: Beta** – tested in a demo environment, not yet in customer production.

**All data in this module is fictional demo data.** It is the data of the fictional
bicycle workshop *Pyöräpaja Demo Oy* shown at <https://plm.rockit.fi> (the company name and
the website theme are not part of this module). Customers (e.g. *Aino Asiakas (demo)*), vendors (*Runkopaja Demo Oy*, *Komponenttitukku
Demo Oy*, …), items, prices and addresses are invented; e-mail addresses use
`example.com`. Product images were generated for the demo and show no brands. The data
is in Finnish.

A made-to-order bicycle workshop from start to finish:

- **Webshop configurator**: a bicycle with Model × Colour × Size × Drivetrain
  (200 combinations); variants are created dynamically when ordered.
- **Two-level attribute BoM**: the bicycle BoM picks a *painted frame* variant, the
  painted frame BoM picks the *raw frame* (five PLM component families, one per model)
  and the *paint* by attribute values.
- **Paint shop and assembly** work centres and operations, MTO and min/max purchasing,
  six fictional vendors with price lists and lead times, invoice export templates.
- **PLM**: raw frames are odooplm items with revisions; a ready change request
  *ECR-0101* lets you show ECR → ECO → new revision → effectivity.

Two small extensions are included because the bicycle attributes are dynamic: a new
variant gets the image matching its attribute values, and the webshop shows the image of
the selected combination before the variant exists.

The demo script (in Finnish) is in [DEMO.md](https://github.com/rockitoy/avoinplm/blob/20.0/rockit_bike_demo/DEMO.md).
