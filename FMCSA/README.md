# FMCSA SMS motor-carrier census

Source: U.S. Department of Transportation, FMCSA SMS Input - Motor Carrier
Census Information (`kjg3-diqy`).

The CSV in this folder was exported on 2026-09-01 with these filters:

- contact email contains `@`
- physical country is `US`
- 1-10 power units
- 1-20 drivers
- federal, state, and local government flags are false
- private passenger non-business is false
- at least one business-use flag is true: authorized for hire, exempt for
  hire, private property, or private passenger business

File inventory:

| File | Data rows | Size | SHA-256 |
|---|---:|---:|---|
| `SMS_Input_-_Motor_Carrier_Census_Information_20260901.csv` | 1,416,632 | 525,512,695 bytes | `2CD86EF3B99F2F24E355601847E070BEB9C345B8C3CB742EC7D7793863F7C1C7` |

The raw CSV is intentionally excluded from Git. Import it with:

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Lead Warehouse"
python .\import_fmcsa.py
```

The importer validates the download, loads typed data into `raw_fmcsa`, and
integrates conservative matches and unmatched carriers into the canonical
`warehouse` schema.
