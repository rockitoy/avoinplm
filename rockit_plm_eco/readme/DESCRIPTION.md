**Status: Beta** – tested in a demo environment, not yet in customer production.

Engineering change orders on top of OmniaGit odooplm *activity_validation* (not modified):

- **ECR → ECO**: when an odooplm change request moves to "ECO", an ECO document is created
  with the request's item as the first affected item (button *Open ECO* on the request).
- **Affected items**: PLM items (templates, variant families included) that get a new
  revision; **BoM versions** (OCA *mrp_bom_version*): sellable/configurable products whose
  BoM gets a new draft version.
- **Effectivity policy** on the ECO, applied when each revision is released: *use up old
  stock first*, *immediately* or *from a date*.
- **Impact analysis** from the ECO: where used (fixed lines; attribute-match lines and
  component families when the configurator modules are installed), stock per revision, open MOs (components and produced), RFQs,
  confirmed POs and open sales of BoM-versioned products.
- **Closing**: when all revisions are released the ECO closes, BoM versions are activated
  (on the date for date effectivity, by a scheduled action), the old versions become
  historical and the ECR is marked done.
