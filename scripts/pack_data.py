"""Pack the raw loan workbook into src/data.json (compact, column-wise, no identifiers).

Usage:  python scripts/pack_data.py [path/to/workbook.xlsx]
Default input: data/dummy-dash-lite.xlsx (git-ignored). Takes ~2 minutes for 100k rows.
Phone numbers and IDs are never written out.
"""
import sys, json, base64, pathlib
import numpy as np, pandas as pd, openpyxl

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'dummy-dash-lite.xlsx'
KEEP = ['loan_status_bf','decision_date_bf','installment_due_date_bf','loan_amount_bf','term_bf',
        'loan_count_with_hakeem_bf','profit_bf','loan_amount_with_service_charges_bf','recovered_amount_bf',
        'loan_amount_disbursed_bf','paid_date_bf','sold_date_bf','dpd_bf',
        'dpd_range_bf','default_7_bf','default_15_bf','default_30_bf','slider_use_bf','early_settlement_bf']

import os
if os.environ.get('PACK_PICKLE'):
    df = pd.read_pickle(os.environ['PACK_PICKLE'])[KEEP].copy()
else:
    ws = openpyxl.load_workbook(src, read_only=True).active
    it = ws.iter_rows(values_only=True)
    head = list(next(it)); idx = [head.index(c) for c in KEEP]
    df = pd.DataFrame([[r[i] for i in idx] for r in it], columns=KEEP)
for c in ['loan_amount_bf','term_bf','loan_count_with_hakeem_bf','profit_bf','loan_amount_with_service_charges_bf',
          'recovered_amount_bf','loan_amount_disbursed_bf','dpd_bf','default_7_bf','default_15_bf','default_30_bf','slider_use_bf','early_settlement_bf']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df[df.loan_status_bf != 'Rejected'].copy()

ts = lambda c: pd.to_datetime(df[c].str[:19])
dd, due = ts('decision_date_bf'), ts('installment_due_date_bf')
D0, ASOF = pd.Timestamp('2026-04-13'), pd.Timestamp('2026-07-09')
day = (dd.dt.normalize() - D0).dt.days
dueo = (due.dt.normalize() - D0).dt.days
asof = (ASOF - D0).days
st = df.loan_status_bf.map({'Active': 0, 'Active in Arrears': 1, 'Closed': 2}).astype(int)
dp = df.dpd_range_bf.map({'Dpd0': 0, 'Dpd7': 1, 'Dpd15': 2, 'Dpd21': 3, 'Dpd30': 4, 'Dpd30+': 5}).astype(int)
mat = lambda n: ((due + pd.Timedelta(days=n)) <= ASOF).astype(int)
I = lambda c: df[c].fillna(0).astype(int)
flags = (I('default_7_bf') + I('default_15_bf') * 2 + I('default_30_bf') * 4 + mat(7) * 8 + mat(15) * 16
         + mat(30) * 32 + I('slider_use_bf') * 64 + I('early_settlement_bf') * 128).astype(int)
paid_ts = pd.to_datetime(df.paid_date_bf.str[:19])
paidd = (paid_ts.dt.normalize() - D0).dt.days.fillna(255).clip(0, 255)
sold_ts = pd.to_datetime(df.sold_date_bf.str[:19])
lagh = ((sold_ts - dd).dt.total_seconds() / 3600).round().clip(0, 254).fillna(255)
cols = {
 'day': (day, np.uint8), 'hour': (dd.dt.hour, np.uint8), 'st': (st, np.uint8), 'dpd': (dp, np.uint8),
 'amt': (df.loan_amount_bf.round(), np.uint16), 'term': (df.term_bf.clip(upper=255), np.uint8),
 'ten': (df.loan_count_with_hakeem_bf.clip(upper=255), np.uint8), 'fl': (flags, np.uint8),
 'profit': (df.profit_bf.fillna(0).clip(lower=0).round(), np.uint16),
 'repay': (df.loan_amount_with_service_charges_bf.round(), np.uint32),
 'rec': (df.recovered_amount_bf.round(), np.uint32), 'due': (dueo, np.uint8),
 'disb': (df.loan_amount_disbursed_bf.fillna(df.loan_amount_bf).round().clip(upper=65535), np.uint16),
 'paid': (paidd, np.uint8), 'lagh': (lagh, np.uint8), 'dpdd': (df.dpd_bf.fillna(0).clip(0, 255), np.uint8)}
out = {'n': len(df), 'asof': asof, 'd0': '2026-04-13', 'c': {}}
for k, (s, t) in cols.items():
    out['c'][k] = base64.b64encode(np.asarray(s).astype(t).tobytes()).decode()
(ROOT / 'src' / 'data.json').write_text(json.dumps(out, separators=(',', ':')))
print('rows', len(df), '-> src/data.json')
