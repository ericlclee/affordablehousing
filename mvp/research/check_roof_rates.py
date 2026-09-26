"""Exploratory sensitivity audit, not a validated room-vs-rooftop-home classifier."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('csv', type=Path, help='Path to the downloaded Foundations CSV')
parser.add_argument('--out', type=Path, default=Path('audit-output'), help='Output directory; defaults to audit-output')
args = parser.parse_args()
SOURCE = args.csv
OUT = args.out
OUT.mkdir(parents=True, exist_ok=True)
with SOURCE.open(newline='') as handle:
    reader = csv.DictReader(handle)
    fields = reader.fieldnames
    rows = list(reader)

roof = re.compile(r'\b(?:roof extension|roof extensions|loft conversion|loft conversions|mansard|dormer|roof enlargement|additional storey|additional storeys|upward extension)\b', re.I)
new = re.compile(r'\b(?:new|additional|create|creation|creating|provide|providing|form|formation|forming|comprising|accommodate)\b.{0,90}\b(?:dwellings?|flats?|apartments?|residential units?|self[- ]contained units?)\b|\bself[- ]contained (?:flat|flats|dwelling|dwellings)\b', re.I)
room = re.compile(r'\b(?:bedroom|bedrooms|room in (?:the )?roof|rooms in (?:the )?roof|habitable|living accommodation|living space|additional accommodation)\b', re.I)
procedural = re.compile(r'\b(?:prior approval|certificate of lawfulness|lawful development certificate|certificate of lawful|discharge of condition|discharge of conditions|variation of condition|variation of conditions|non[- ]material amendment|minor material amendment)\b', re.I)

roof_rows = [row for row in rows if roof.search(row['description'])]
cohorts = {
    'all_roof_keywords': roof_rows,
    'roof_and_new_home_language': [r for r in roof_rows if new.search(r['description'])],
    'roof_and_room_language_without_new_home_language': [r for r in roof_rows if room.search(r['description']) and not new.search(r['description'])],
    'roof_without_new_home_language': [r for r in roof_rows if not new.search(r['description'])],
}

def results(records):
    granted = sum(r['status'] in ('Permitted', 'Conditions') for r in records)
    refused = sum(r['status'] == 'Rejected' for r in records)
    return {'all_records':len(records), 'granted_status':granted, 'refused_status':refused,
            'decided_denominator':granted+refused,
            'approval_percent':100*granted/(granted+refused) if granted+refused else None,
            'status_counts':dict(Counter(r['status'] for r in records))}

summary = {
    'warning':'Exploratory text filters only. Not validated rooftop-new-home versus existing-home-room categories. Does not reproduce the original 75%/56% claim.',
    'source_file':SOURCE.name, 'source_url':'https://foreman.house-london.uk/download/csv/',
    'source_bytes':SOURCE.stat().st_size, 'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rows':len(rows), 'fields':fields,
    'duplicate_names':len(rows)-len({r['name'] for r in rows}),
    'missing_n_dwellings':sum(not r['n_dwellings'] for r in rows),
    'start_date_min':min(r['start_date'] for r in rows if r['start_date']),
    'start_date_max':max(r['start_date'] for r in rows if r['start_date']),
    'regexes':{'roof':roof.pattern,'new':new.pattern,'room':room.pattern,'exclude_procedural':procedural.pattern},
    'cohorts':{}
}
for label, records in cohorts.items():
    full=[r for r in records if r['app_type']=='Full']
    summary['cohorts'][label]={
        'all_types':results(records), 'full_type':results(full),
        'full_type_excluding_obvious_procedural_text':results([r for r in full if not procedural.search(r['description'])])
    }
with (OUT/'roof_rate_audit.json').open('w') as handle:
    json.dump(summary,handle,indent=2)
sample_fields=['name','area_name','app_type','status','decision','description','url']
with (OUT/'roof_new_language_samples.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=sample_fields)
    writer.writeheader()
    for r in cohorts['roof_and_new_home_language']:
        if r['app_type']=='Full': writer.writerow({k:r[k] for k in sample_fields})
print(json.dumps({k:v for k,v in summary.items() if k not in ('fields','regexes')},indent=2))
