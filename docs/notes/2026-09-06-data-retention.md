# Data retention and token handling — 2026-09-06

- History is written locally to the active save directory as
  `lorekeeper-history.jsonl`.
- History is not copied into the repository, uploaded automatically, or sent
  to the model by the collector.
- The collector is disabled by default and can be stopped with
  `lorekeeper/collect stop`.
- Raw values remain in history so translations can be regenerated later.
- The runtime token catalog is version-specific. Use `lorekeeper/tokens` or
  `lorekeeper/tokens copy` against the active DF/DFHack installation rather
  than treating a checked-in catalog as universal.
- Future history UI and helper-service work must make retention, export, and
  deletion controls explicit before sharing data outside the local save.
