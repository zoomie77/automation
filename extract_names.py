#!/usr/bin/env python3
"""
clean_names.py — extract clean, lowercase, sorted names from a messy
tab-separated LinkedIn-style scrape.

Usage:
    python3 clean_names.py input.txt                 # prints to screen
    python3 clean_names.py input.txt -o names.txt    # writes to a file

What it does:
    - repairs double-encoded UTF-8 accents (José, Muñoz, ...)
    - keeps the person's name, drops job titles / "LinkedIn" /
      follower counts / profile URLs / country-domain tags
    - lowercases, sorts A-Z, removes duplicates
"""
import re, sys, argparse, unicodedata

TITLE = re.compile(r'\s+(Systempreneur|Certified|AI|Head|Partner|Co-Owner|Co-Founder|'
                   r'Administrador|Producer|Digital|Director|Manager|Engineer|Lead|'
                   r'Scientist|Officer|Owner|Teacher|Student|Analyst|Consultant|'
                   r'Specialist|Sommelier|Geologist|Lawyer|Attorney|Self|Retired|'
                   r'Siswa|Mahasiswa|Operator|Gerente|Supervisor|President|Founder)\b.*$', re.I)
SUFFIX = re.compile(r'\s*,\s*(PMP|Esq\.?|M\.?B\.?A\.?|CSI|SE|PhD|Ph\.?D\.?|CPA)\b.*$', re.I)
ACCENTS = [('Ã©','é'),('Ã¼','ü'),('Ã±','ñ'),('Ã³','ó'),('Ã¡','á'),('Ã­','í'),('Ã¨','è'),('Ãº','ú')]

def demojibake(t):
    try:
        return t.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return t

def fix_accents(n):
    for a, b in ACCENTS:
        n = n.replace(a, b)
    n = re.sub(r'Ã(?=[a-z])', 'í', n)      # orphaned accent mid-word
    n = re.sub(r'Ã$', 'í', n)
    return n

def strip_specials(n):
    # accents -> nearest ASCII letter (josé -> jose), not deletion
    n = unicodedata.normalize('NFKD', n)
    n = ''.join(c for c in n if not unicodedata.combining(c))
    n = n.replace('ø', 'o').replace('Ø', 'O').replace('ß', 'ss').replace('æ', 'ae')
    n = n.replace('-', ' ')                 # compound names stay two words
    n = re.sub(r"[^A-Za-z0-9 ]", '', n)     # drop ( ) . , ' etc.
    return re.sub(r'\s{2,}', ' ', n).strip()

def extract(line):
    s = demojibake(line.rstrip('\r\n'))
    if not s.strip():
        return None
    fields = [c.strip() for c in s.split('\t')]
    name = None
    m = re.search(r'·\s*(.+)', s)                       # clean display name after "·"
    if m:
        tail = re.split(r'\s+\d[\d.,]*[KkMm]?\+?\s*followers', m.group(1))[0]
        tail = re.split(r'\s+https?://', tail)[0]
        tail = re.split(r'\s+\d+\s*follower', tail)[0]
        cand = tail.strip(' ,.-')
        if cand and len(cand.split()) <= 6 and 'LinkedIn' not in cand:
            name = cand
    if not name:                                        # fallback: leading name columns
        parts = []
        for c in fields:
            if not c:
                continue                      # skip empty leading columns
            low = c.lower()
            if 'linkedin' in low or 'http' in low or '·' in c or '@' in c:
                break
            if len(c.split()) > 2:            # a long blob = a job title, stop
                break
            parts.append(c)
        name = ' '.join(parts).strip(' ,.-')
    if not name:
        return None
    name = fix_accents(demojibake(name))
    name = TITLE.sub('', SUFFIX.sub('', name))
    name = re.sub(r'\s{2,}', ' ', name).strip(' ,.-')
    name = strip_specials(name)
    return name or None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('-o', '--output')
    args = ap.parse_args()
    with open(args.input, encoding='utf-8') as f:
        names = {extract(l) for l in f}
    names.discard(None)
    out = '\n'.join(sorted(n.lower() for n in names)) + '\n'
    if args.output:
        open(args.output, 'w', encoding='utf-8').write(out)
        print(f'Wrote {out.count(chr(10))} names to {args.output}')
    else:
        sys.stdout.write(out)

if __name__ == '__main__':
    main()
