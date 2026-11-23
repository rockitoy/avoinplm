- System parameter `rockit_plm_variant_default_code.revision_in_code` (boolean): set it
  to restore odooplm's `CODE_REV` internal references.
- Existing databases: run `tools/pre_install_product_variant_default_code.sql` (in this
  repository) once *before* installing *product_variant_default_code*.
