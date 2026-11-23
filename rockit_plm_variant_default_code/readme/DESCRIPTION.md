**Status: Beta** – tested in a demo environment, not yet in customer production.

Internal references for PLM items when the revision is shown as its own field:

- odooplm's automatic internal reference (`plm_auto_internalref`) no longer appends the
  revision: a single item keeps the code `ENG-CODE` in every revision. Set the system
  parameter `rockit_plm_variant_default_code.revision_in_code` to restore `CODE_REV`.
- Variant families (a PLM template with several attribute values) get per-variant codes
  from `product_variant_default_code` (reference prefix + attribute value codes); odooplm's
  automatic code is switched off for them, as it would give every variant the same code.
- A new revision keeps the prefix, the mask and the generated codes; hand-set codes are
  copied.
