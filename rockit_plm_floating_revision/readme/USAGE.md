1. Use PLM items (odooplm engineering parts) as components, either directly on BoM lines
   or through *Component (product template)* / *Component families*.
2. *Floating revision* is on by default on every BoM line. Untick it to pin a line to
   exactly the revision on the line. The *Revision* column shows `↻` for floating lines.
3. On a revision set *Phase-out when superseded*: *Use up free stock first* (default) or
   *Immediately*. *Effective from* is set on release when left empty; set it beforehand
   for a future effectivity date.
4. Create a new revision with odooplm's *New Revision*: variants, internal references,
   cost, vendor prices, routes, documents and BoMs are carried over.
5. Release the revision (*Release Component*). Reordering rules move to the new revision
   and a chatter note lists open orders on older revisions.
6. On the product, *Open orders* proposes moving unstarted MO components, draft MOs and
   RFQ lines to the revision effective at their date.
