-- Run ONCE before installing product_variant_default_code in an existing database.
-- The module turns product.product.default_code into a stored computed field; on install
-- it would recompute (overwrite) every existing internal reference, and generate codes
-- for variants without one. Marking every existing variant "manual reference" keeps the
-- data exactly as it is; families are switched to generated codes one by one afterwards
-- (untick "Manual Reference" or let rockit_plm_variant_default_code do it).
ALTER TABLE product_product ADD COLUMN IF NOT EXISTS manual_code boolean;
UPDATE product_product SET manual_code = TRUE;
