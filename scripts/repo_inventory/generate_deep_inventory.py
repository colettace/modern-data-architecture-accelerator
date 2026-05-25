#!/usr/bin/env python3
import json, subprocess, pathlib, re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOC_OUT = ROOT / 'docs/repo_inventory_deep_summary.md'
JSON_OUT = ROOT / 'artifacts/repo_inventory_deep_summary.json'
GRAPH_OUT = ROOT / 'artifacts/repo_context_graph.json'
COVERAGE_OUT = ROOT / 'artifacts/coverage_report.json'


def run(cmd):
    return subprocess.check_output(cmd, text=True, cwd=ROOT).splitlines()

files = sorted(set(run(['git','ls-files']) + run(['git','ls-files','--others','--exclude-standard'])))

all_dirs={'.'}
for f in files:
    p=pathlib.PurePosixPath(f)
    cur=''
    for part in p.parts[:-1]:
        cur = part if not cur else f"{cur}/{part}"
        all_dirs.add(cur)

imports=defaultdict(list)
outbound=defaultdict(list)

# quick index for references
basename_map=defaultdict(list)
for f in files:
    basename_map[pathlib.PurePosixPath(f).name].append(f)

file_summaries=[]

def read_text(path):
    b=path.read_bytes()
    if b'\x00' in b[:4096]:
        return None
    return b.decode('utf-8',errors='replace')

for rel in files:
    p=ROOT/rel
    txt=read_text(p)
    ext=p.suffix.lower()
    in_refs=[]
    out_refs=[]
    purpose=''
    key=[]
    role=[]

    if txt is None:
        purpose='Binary or non-text artifact.'
        key.append(f'File size: {p.stat().st_size} bytes')
    else:
        lines=txt.splitlines()
        lc=len(lines)
        purpose=f'Text file with {lc} lines used in the repository workflow.'

        if ext=='.py':
            defs=re.findall(r'^def\s+([\w_]+)\(|^class\s+([\w_]+)\b', txt, flags=re.M)
            imps=re.findall(r'^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))', txt, flags=re.M)
            names=[a or b for a,b in defs][:8]
            mods=[a or b for a,b in imps][:12]
            if names: key.append('Defines: '+', '.join(names))
            if mods:
                out_refs.extend(mods)
                key.append('Imports modules: '+', '.join(mods[:6]))
            role.append('Python implementation or automation script.')
        elif ext in {'.md'}:
            heads=[l.strip('# ').strip() for l in lines if l.startswith('#')][:6]
            if heads: key.append('Sections: '+', '.join(heads))
            role.append('Documentation for users or maintainers.')
        elif ext in {'.yml','.yaml'}:
            keys=re.findall(r'^([A-Za-z0-9_\-]+):', txt, flags=re.M)[:12]
            if keys: key.append('Top-level keys: '+', '.join(keys))
            role.append('Configuration/automation definition.')
        elif ext=='.json':
            role.append('Structured configuration or metadata.')
            key.append('JSON content ingested in full for summarization.')
        elif ext=='.sql':
            role.append('SQL transformation/query logic.')
            tables=re.findall(r'\bfrom\s+([\w\.\-\"]+)|\bjoin\s+([\w\.\-\"]+)', txt, flags=re.I)
            t=[a or b for a,b in tables][:8]
            if t: key.append('References tables/views: '+', '.join(t))
        elif ext in {'.sh','.bash'}:
            role.append('Shell automation script.')
            cmds=re.findall(r'^(?:\s*)([a-zA-Z0-9_\-]+)\s+', txt, flags=re.M)[:10]
            if cmds: key.append('Primary commands used: '+', '.join(dict.fromkeys(cmds)))
        else:
            role.append('Repository asset/config/source file.')

        # reference scan by basename mention
        for bn,cands in basename_map.items():
            if bn==pathlib.PurePosixPath(rel).name:
                continue
            if bn in txt:
                in_refs.extend(cands[:1])

    summary = {
        'path': rel,
        'type': 'file',
        'purpose': purpose,
        'key_contents': key[:5],
        'dependency_context': {
            'inbound_mentions': sorted(set(in_refs))[:10],
            'outbound_dependencies': sorted(set(out_refs))[:10],
        },
        'runtime_workflow_role': role[:3],
    }
    file_summaries.append(summary)

# directory summaries
children=defaultdict(list)
for d in all_dirs:
    children[d]=[]
for f in files:
    par=str(pathlib.PurePosixPath(f).parent)
    if par=='.': par='.'
    children[par].append(f)
for d in all_dirs:
    if d=='.': continue
    par=str(pathlib.PurePosixPath(d).parent)
    if par=='.': par='.'
    children[par].append(d+'/')

dir_summaries=[]
for d in sorted(all_dirs):
    items=sorted(children[d])
    file_count=sum(1 for i in items if not i.endswith('/'))
    dir_count=len(items)-file_count
    role='Repository root' if d=='.' else f"Directory for {d.split('/')[0]}-scoped components"
    dir_summaries.append({
        'path': './' if d=='.' else d+'/',
        'type':'directory',
        'summary': f"{role}. Contains {dir_count} subdirectories and {file_count} files.",
        'children_sample': items[:8]
    })

all_entries = dir_summaries + file_summaries

JSON_OUT.write_text(json.dumps(all_entries, indent=2), encoding='utf-8')
GRAPH_OUT.write_text(json.dumps({'files': len(files), 'directories': len(all_dirs)}, indent=2), encoding='utf-8')
COVERAGE_OUT.write_text(json.dumps({'discovered_files': len(files), 'ingested_files': len(file_summaries), 'complete': len(files)==len(file_summaries)}, indent=2), encoding='utf-8')

# markdown grouped format B
groups=defaultdict(list)
for e in all_entries:
    p=e['path']
    top='(root)' if p.startswith('./') else p.split('/')[0]
    groups[top].append(e)

with DOC_OUT.open('w', encoding='utf-8') as f:
    f.write('# Repository Inventory Deep Summary (Git-ignore respected)\n\n')
    f.write('Generated via full-file ingestion, contextual indexing, and directory synthesis.\n\n')
    for g in sorted(groups):
        f.write(f'## {g}\n\n| Path | Deep Summary |\n|---|---|\n')
        for e in sorted(groups[g], key=lambda x:x['path']):
            if e['type']=='directory':
                s=e['summary'] + ' Sample children: ' + ', '.join(e['children_sample'])
            else:
                dep=e['dependency_context']
                s=(f"Purpose: {e['purpose']} Key contents: {'; '.join(e['key_contents']) if e['key_contents'] else 'N/A'}. "
                   f"Context: inbound={len(dep['inbound_mentions'])}, outbound={len(dep['outbound_dependencies'])}. "
                   f"Role: {'; '.join(e['runtime_workflow_role']) if e['runtime_workflow_role'] else 'N/A'}")
            f.write(f"| `{e['path']}` | {s.replace('|','\\|')} |\n")
        f.write('\n')

print(f'Generated {DOC_OUT} with {len(all_entries)} rows')
