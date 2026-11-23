**Status: Beta** – tested in a demo environment, not yet in customer production.

Use-time ("floating") PLM revisions in manufacturing, on top of OmniaGit odooplm
(not modified). Works on its own with fixed BoM lines. With the configurator modules of
[odoo-konfiguraattori](https://github.com/rockitoy/odoo-konfiguraattori) the bridge
module *rockit_plm_component_family_bridge* (installed automatically) makes
attribute-matched lines and component families float too.

- **Floating BoM lines** (default, per line): lines whose component is a PLM item use the revision that is released and effective at the
  MO's planned start. The BoM itself is not edited when a revision is released.
- **Use up superseded revisions**: free stock of older revisions marked *Use up* is
  consumed first, for the MO's full quantity and counted in the MO's source location
  (and children). A line can be split over two revisions (e.g. 2 × rev 0 + 3 × rev 1).
- **Carry-over on new revision**: odooplm copies the template only. Variants (also for
  dynamic attributes), internal references, cost, vendor prices, routes and variant
  documents are carried over; with *Document revision* every variant's documents are
  revised. The BoMs of the old revision are copied to the new one when it has none.
  On release the reordering rules move to the new revision.
- **BoM cost and BoM structure report** use the revision effective now.
- **Revision column** (SAP style, not in the name) on products, BoM lines, MO
  components, purchase lines and stock moves.
- **Phase-in replenishment**: a reordering rule of the current revision counts the
  forecasted stock of superseded *Use up* revisions (column *Superseded revision stock*),
  so the new revision is bought only for what the old stock does not cover; a shortage
  of the old revision is passed on to the new one (as SAP discontinuation). Stock moves
  of the old revision recompute the new revision's rules. Manual reordering rules
  created by the replenishment report for a superseded revision are merged into the
  current revision's rule.
- **Release impact** (*Open orders* on the product, and a chatter note on release): not
  started MO components and RFQ lines on older revisions are proposed to move to the
  revision effective at their date (old stock that is used up first stays), with the new
  revision's vendor price; draft MOs that produce an older revision are moved to the
  current revision and its BoM; confirmed purchase orders and MOs are listed only. A planned date in the past counts as "now".
- **Access**: a PLM engineer (OdooPLM *Integration User* + *Products: Create*) can create a
  revision and a *Release User* can release it without being an inventory, purchase or
  website administrator. The transferred records only (vendor prices and extra product
  images of the item's revisions on a new revision, its reordering rules on release, the
  manual rules the replenishment report creates for superseded revisions) are written with
  sudo, limited to the user's companies. *Release Component* checks the *Release Users*
  group on the server too, not only in the view.
