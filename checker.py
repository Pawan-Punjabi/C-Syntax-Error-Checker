import re
from typing import List, Dict, Tuple
import itertools
import difflib


def remove_comments(code: str) -> str:
    """Remove C single-line (//) and multi-line (/* */) comments."""
    # Remove /* */ comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    # Remove // comments
    code = re.sub(r'//.*', '', code)
    return code


def preprocess(code: str) -> List[str]:
    """Normalize line endings, remove comments and strip trailing spaces.

    Returns list of lines.
    """
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    code = remove_comments(code)
    lines = [ln.rstrip() for ln in code.split('\n')]
    return lines


def is_valid_identifier(name: str) -> bool:
    return re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) is not None


def edits1(word: str) -> List[str]:
    # used for very small fuzzy keyword checking (one-edit distance)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + (R[1:] if R else '') for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return list(set(deletes + transposes + replaces + inserts))


_C_KEYWORDS = {
    'auto','break','case','char','const','continue','default','do','double','else','enum',
    'extern','float','for','goto','if','inline','int','long','register','restrict','return',
    'short','signed','sizeof','static','struct','switch','typedef','union','unsigned','void',
    'volatile','while','_Bool','_Complex','_Imaginary'
}
# Common C identifiers to avoid false positives in keyword typo detection
_SAFE_WORDS = {'main', 'printf', 'scanf', 'include', 'stdio', 'h', 'size_t', 'NULL'}


def find_syntax_errors(code: str) -> List[Dict]:
    """Run several lightweight syntax checks on C source text.

    This is not a full parser. It implements heuristic checks mentioned in the spec:
    - invalid variable names (start with digit or contain special char)
    - missing semicolons for simple statements
    - incorrect/typoed keywords (one edit away from real keyword)
    - unclosed quotes

    Returns a list of error dicts: {'line': int, 'type': str, 'message': str}
    """
    lines = preprocess(code)
    errors: List[Dict] = []

    # 1) Check includes and usage (stdio)
    include_stdio_ok = False
    include_stdio_semicolon_error = None
    include_pattern = re.compile(r'#\s*include\s*<\s*stdio\.h\s*>\s*;?')
    for idx, ln in enumerate(lines, start=1):
        m = include_pattern.search(ln)
        if m:
            # if ends with semicolon report error
            if ln.strip().endswith(';'):
                include_stdio_semicolon_error = idx
            else:
                include_stdio_ok = True

    # 2) Bracket and quote matching using a stack
    opening = {'(': ')', '{': '}', '[': ']'}
    closing = {')': '(', '}': '{', ']': '['}
    stack: List[Tuple[str, int]] = []
    in_single = False
    in_double = False
    escape = False
    for idx, ln in enumerate(lines, start=1):
        i = 0
        while i < len(ln):
            ch = ln[i]
            # handle escape inside quotes
            if ch == '\\' and (in_single or in_double):
                i += 2
                continue
            # double quote handling
            if ch == '"' and not in_single:
                if in_double:
                    # close double quote and remove the matching quote entry from stack if present
                    in_double = False
                    # pop the last '"' entry if it exists
                    for j in range(len(stack)-1, -1, -1):
                        if stack[j][0] == '"':
                            stack.pop(j)
                            break
                else:
                    in_double = True
                    stack.append(('"', idx))
            # single quote handling
            elif ch == "'" and not in_double:
                if in_single:
                    in_single = False
                    for j in range(len(stack)-1, -1, -1):
                        if stack[j][0] == "'":
                            stack.pop(j)
                            break
                else:
                    in_single = True
                    stack.append(("'", idx))
            # only consider brackets when not inside quotes
            elif not in_single and not in_double:
                if ch in opening:
                    stack.append((ch, idx))
                elif ch in closing:
                    # find matching opening at top
                    if stack and stack[-1][0] == closing[ch]:
                        stack.pop()
                    else:
                        errors.append({'line': idx, 'type': 'Mismatched bracket', 'message': f'Unmatched closing "{ch}" at line {idx}'})
            i += 1

    # Any remaining items in stack are unclosed
    for sym, ln_num in stack:
        if sym in ('"', "'"):
            errors.append({'line': ln_num, 'type': 'Unclosed quote', 'message': f'Unclosed {sym} starting on line {ln_num}'})
        else:
            errors.append({'line': ln_num, 'type': 'Unclosed bracket', 'message': f'Unclosed "{sym}" starting on line {ln_num}'})

    # include errors
    if include_stdio_semicolon_error is not None:
        errors.append({'line': include_stdio_semicolon_error, 'type': 'Include error', 'message': 'Do not put semicolon after #include<stdio.h>'})

    # 3) Check for scanf usage without stdio include
    for idx, ln in enumerate(lines, start=1):
        if 'scanf' in ln and not include_stdio_ok:
            errors.append({'line': idx, 'type': 'Missing include', 'message': 'Use of scanf without including <stdio.h>'})

    # 4) Simple main return-type check: look for a "main("
    for idx, ln in enumerate(lines, start=1):
        if re.search(r'\bmain\s*\(', ln):
            # try to get the tokens before main on same line
            prefix = ln.split('main')[0]
            if not re.search(r'\b(int|void|char|long|short|signed|unsigned)\b', prefix):
                # maybe return type on previous line (simple heuristic)
                prev = lines[idx-2] if idx - 2 >= 0 else ''
                if not re.search(r'\b(int|void|char|long|short|signed|unsigned)\b', prev):
                    errors.append({'line': idx, 'type': 'Missing return type', 'message': 'Function main must have a return type (e.g., int main)'} )

    # 5) Declaration and semicolon heuristics
    decl_pattern = re.compile(r'\b(?:unsigned|signed|long|short|int|char|float|double)\b\s+([^;=,]+)')

    # valid operators (arithmetic and arithmetic-assignment)
    valid_ops = {'+', '-', '*', '/', '%', '++', '--', '+=', '-=', '*=', '/=', '%=', '='}
    # list of multi-char operators to detect first
    multi_ops = ['++', '--', '+=', '-=', '*=', '/=', '%=', '==', '!=', '<=', '>=', '&&', '||', '<<', '>>']

    for i, ln in enumerate(lines, start=1):
        s = ln.strip()
        if not s:
            continue
        # ignore preprocessor directives except include checks already done
        if s.startswith('#'):
            continue

        # Check missing semicolon for simple assignment/declaration/return/expr lines
        if (('=' in s or s.startswith('return') or re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*\(', s))) and not s.endswith(';') and not s.endswith('{') and not s.endswith('}'):
            # allow for control statements
            if not re.match(r'^(if|for|while|switch)\b', s):
                errors.append({'line': i, 'type': 'Missing semicolon', 'message': f'Line {i} may be missing a terminating ";"'})

        # Check invalid variable names in simple declarations
        m = decl_pattern.search(s)
        if m:
            # the group may contain multiple declarators separated by comma
            names = [part.strip() for part in m.group(1).split(',')]
            for nm in names:
                # remove initializer if present
                nm_clean = nm.split('=')[0].strip()
                # strip array brackets
                nm_clean = nm_clean.split('[')[0].strip()
                # skip function definitions / declarations (e.g., "main() {")
                if '(' in nm_clean or ')' in nm_clean or '{' in nm_clean:
                    continue
                if not is_valid_identifier(nm_clean):
                    errors.append({'line': i, 'type': 'Invalid variable name', 'message': f'"{nm_clean}" is not a valid identifier'})

        # Operator checks: locate operators and verify they are allowed
        # first detect multi-char operators
        ops_found = []
        temp = s
        for op in multi_ops:
            if op in temp:
                # find all occurrences
                for _ in re.finditer(re.escape(op), temp):
                    ops_found.append(op)
                # remove them so we don't double count
                temp = temp.replace(op, ' ')
        # now single-char operators
        for ch in ['+', '-', '*', '/', '%', '=', '&', '|', '^', '~', '!', '<', '>','?',':']:
            if ch in temp:
                for _ in re.finditer(re.escape(ch), temp):
                    ops_found.append(ch)

        for op in ops_found:
            if op not in valid_ops:
                errors.append({'line': i, 'type': 'Invalid operator', 'message': f'Operator "{op}" is not allowed (only arithmetic operators allowed)'})

        # Check for probable typoed keywords: look at tokens that are alphabetic and short
        # We use a regex that also captures optional following parentheses to identify function calls
        for match in re.finditer(r"\b([a-zA-Z_]{2,20})\b(\s*\()?", s):
            tk = match.group(1)
            is_func_call = match.group(2) is not None
            
            if tk in _C_KEYWORDS or tk in _SAFE_WORDS:
                continue
            
            # If it's a function call, it's likely an intentional identifier (function name)
            # We only check for typos of keywords that are actually followed by parens
            paren_keywords = {'if', 'for', 'while', 'switch', 'sizeof', 'return'}
            
            matched_kw = None
            tk_lower = tk.lower()
            
            # 1. Case-insensitive check
            for kw in _C_KEYWORDS:
                if tk_lower == kw.lower():
                    matched_kw = kw
                    break
            
            # 2. Fuzzy match using difflib with a more conservative cutoff (0.7)
            # This avoids false positives like 'greet' -> 'return' (ratio 0.54)
            if not matched_kw:
                # If it's a function call, only compare against relevant keywords
                search_space = _C_KEYWORDS
                cutoff = 0.7
                
                if is_func_call:
                    search_space = paren_keywords
                    cutoff = 0.8 # Higher threshold for function calls
                
                matches = difflib.get_close_matches(tk, search_space, n=1, cutoff=cutoff)
                if matches:
                    matched_kw = matches[0]
            
            # 3. Fallback to existing edits1 logic for very short words
            if not matched_kw and not is_func_call:
                for kw in _C_KEYWORDS:
                    if tk in edits1(kw) or kw in edits1(tk):
                        matched_kw = kw
                        break
            
            if matched_kw:
                errors.append({'line': i, 'type': 'Incorrect keyword', 'message': f'"{tk}" looks like a typo of C keyword "{matched_kw}"'})

    # if stdio include not found at all, report missing but only once (line 1)
    if not include_stdio_ok and include_stdio_semicolon_error is None:
        # report at top of file
        errors.append({'line': 1, 'type': 'Missing include', 'message': 'Missing #include <stdio.h>'})

    return errors



