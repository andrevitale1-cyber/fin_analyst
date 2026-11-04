"""Public-source smoke check. Does not generate analyses or use paid web search."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_pipeline import fetch_release, ReleaseError

parser=argparse.ArgumentParser()
parser.add_argument('--companies',nargs='+',required=True)
parser.add_argument('--year',type=int,required=True)
parser.add_argument('--quarter',type=int,choices=(1,2,3,4),required=True)
args=parser.parse_args()
failed=False
for company in args.companies:
    try:
        doc=fetch_release(company,args.year,args.quarter,allow_web=False,refresh=True)
        print(json.dumps({'company':company,'status':'found','source':doc.url,'characters':len(doc.text),'sources':doc.sources}))
    except (ReleaseError,ValueError,TimeoutError) as exc:
        failed=True
        print(json.dumps({'company':company,'status':getattr(exc,'code',type(exc).__name__)}))
raise SystemExit(1 if failed else 0)
