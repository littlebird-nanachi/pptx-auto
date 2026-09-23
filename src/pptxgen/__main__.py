import argparse
from .pipeline import generate, approve_html

parser = argparse.ArgumentParser(description='HTML review → approval → PNG/PPTX')
parser.add_argument('--input', help='Slide JSON (required for initial HTML render)')
parser.add_argument('--output', default='output')
parser.add_argument('--theme', default='default')
parser.add_argument('--ratio', choices=['16:9','4:3'], default='16:9')
parser.add_argument('--approve', action='store_true', help='Package already reviewed HTML/PNG into PPTX')
args = parser.parse_args()
if args.approve:
    report = approve_html(args.output)
else:
    if not args.input: parser.error('--input is required unless --approve is used')
    report = generate(args.input,args.output,args.theme,args.ratio,approve=False)
print(f"{report['status']}: {args.output}/qa_report.json")
if report['generated']:
    print(f'{args.output}/presentation.pptx')
else:
    for issue in report['issues']:
        print(issue['detail'])
raise SystemExit(0 if report['generated'] else 1)
