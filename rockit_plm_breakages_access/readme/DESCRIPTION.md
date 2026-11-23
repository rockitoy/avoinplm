**Status: Beta** – tested in a demo environment, not yet in customer production.

odooplm *plm_breakages* computes the breakage counters of BoMs, BoM lines, manufacturing
orders and products as the current user. A user without PLM rights (for example a
production operator with only Manufacturing / User) gets "You are not allowed to access
'PLM Breakages'" when opening a BoM or an MO. With this module the counters are 0 for such
users; PLM users see the real counts. Installed automatically with *plm_breakages*.
