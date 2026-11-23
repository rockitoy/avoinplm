Install `product_variant_default_code` in an existing database only after running
`tools/pre_install_product_variant_default_code.sql` (marks all existing references manual so the
install does not rewrite them). Then, per family: give the attribute values a code, set the
template "Reference Prefix" and untick "Manual Reference" on its variants.
