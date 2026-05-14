from checker import find_syntax_errors


def test_invalid_identifier():
    src = 'int 1x = 5;'
    errs = find_syntax_errors(src)
    assert any(e['type'] == 'Invalid variable name' for e in errs)


def test_missing_semicolon():
    src = 'int x = 5\nint y = 6;'
    errs = find_syntax_errors(src)
    assert any(e['type'] == 'Missing semicolon' for e in errs)


def test_unclosed_quote():
    src = 'char *s = "hello;'
    errs = find_syntax_errors(src)
    assert any('Unclosed quote' in e['type'] or 'Unclosed quote' in e['message'] for e in errs)
