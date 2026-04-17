import os


def tokenise(expression: str) -> list[tuple[str, str]]:
    tokens = []
    i = 0
    text = expression.strip()

    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or (ch == '.' and i + 1 < len(text) and text[i + 1].isdigit()):
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                j += 1
            num_str = text[i:j]
            if num_str.count('.') > 1:
                raise ValueError(f"Invalid number literal: {num_str!r}")
            tokens.append(('NUM', num_str))
            i = j
            continue


        if ch in '+-*/':
            tokens.append(('OP', ch))
            i += 1
            continue

        if ch == '(':
            tokens.append(('LPAREN', '('))
            i += 1
            continue

        if ch == ')':
            tokens.append(('RPAREN', ')'))
            i += 1
            continue

        raise ValueError(f"Unrecognised character: {ch!r}")

    tokens.append(('END', ''))
    return tokens


def format_tokens(tokens: list[tuple[str, str]]) -> str:
    parts = []
    for typ, val in tokens:
        if typ == 'END':
            parts.append('[END]')
        else:
            parts.append(f'[{typ}:{val}]')
    return ' '.join(parts)


def tree_to_str(node) -> str:
    kind = node[0]
    if kind == 'num':
        return _format_number(node[1])
    if kind == 'unary':
        return f'(neg {tree_to_str(node[2])})'
    if kind == 'binop':
        return f'({node[1]} {tree_to_str(node[2])} {tree_to_str(node[3])})'
    raise ValueError(f"Unknown node kind: {kind!r}")



def _peek(tokens: list, pos: int) -> tuple[str, str]:
    return tokens[pos]


def parse_expr(tokens: list, pos: int):
    node, pos = parse_term(tokens, pos)

    while True:
        typ, val = _peek(tokens, pos)
        if typ == 'OP' and val in ('+', '-'):
            pos += 1
            right, pos = parse_term(tokens, pos)
            node = ('binop', val, node, right)
        else:
            break

    return node, pos


def parse_term(tokens: list, pos: int):
    node, pos = parse_unary(tokens, pos)

    while True:
        typ, val = _peek(tokens, pos)

        if typ == 'OP' and val in ('*', '/'):
            pos += 1
            right, pos = parse_unary(tokens, pos)
            node = ('binop', val, node, right)

        elif typ in ('NUM', 'LPAREN'):
            right, pos = parse_unary(tokens, pos)
            node = ('binop', '*', node, right)

        else:
            break

    return node, pos


def parse_unary(tokens: list, pos: int):
    typ, val = _peek(tokens, pos)

    if typ == 'OP' and val == '-':
        pos += 1
        operand, pos = parse_unary(tokens, pos)   
        return ('unary', 'neg', operand), pos

    if typ == 'OP' and val == '+':
        raise ValueError("Unary '+' is not supported")

    return parse_primary(tokens, pos)


def parse_primary(tokens: list, pos: int):
    typ, val = _peek(tokens, pos)

    if typ == 'NUM':
        pos += 1
        return ('num', float(val)), pos

    if typ == 'LPAREN':
        pos += 1                             
        node, pos = parse_expr(tokens, pos)  
        typ2, val2 = _peek(tokens, pos)
        if typ2 != 'RPAREN':
            raise ValueError(f"Expected ')' but got {typ2}:{val2!r}")
        pos += 1                             
        return node, pos

    raise ValueError(f"Unexpected token {typ}:{val!r}")


def parse(tokens: list):
    node, pos = parse_expr(tokens, 0)
    typ, val = _peek(tokens, pos)
    if typ != 'END':
        raise ValueError(f"Unexpected token after expression: {typ}:{val!r}")
    return node

def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f'{value:.4f}'



# SINGLE-EXPRESSION EVALUATION (with per-stage error isolation)


def _evaluate_one(expression: str) -> dict:
  


    record = {
        'input':  expression,
        'tree':   'ERROR',
        'tokens': 'ERROR',
        'result': 'ERROR',
    }

    # Stage 1: tokenise 
    try:
        tokens = tokenise(expression)
        record['tokens'] = format_tokens(tokens)
    except Exception:
        return record           

    # Stage 2: parse 
    try:
        tree = parse(tokens)
        record['tree'] = tree_to_str(tree)
    except Exception:
        return record           

    # Stage 3: evaluate 
    try:
        record['result'] = eval_tree(tree)
    except Exception:
        record['result'] = 'ERROR'

    return record


# FILE I/O


def _write_output(output_path: str, results: list[dict]) -> None:
   
    # Write all result dicts to *output_path* using the required format:
   
    lines = []
    for i, rec in enumerate(results):
        if isinstance(rec['result'], float):
            result_str = _format_number(rec['result'])
        else:
            result_str = rec['result']      # 'ERROR'

        lines.append(f"Input: {rec['input']}")
        lines.append(f"Tree: {rec['tree']}")
        lines.append(f"Tokens: {rec['tokens']}")
        lines.append(f"Result: {result_str}")

        if i < len(results) - 1:
            lines.append('')                # blank separator between blocks

    with open(output_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


def evaluate_file(input_path: str) -> list[dict]:
   
    input_path  = os.path.abspath(input_path)
    output_path = os.path.join(os.path.dirname(input_path), 'output.txt')

    with open(input_path, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()

    results = [_evaluate_one(line.rstrip('\n')) for line in lines]
    _write_output(output_path, results)
    return results



# SELF-TEST  (run with: python evaluator.py)

if __name__ == '__main__':
    import sys
    import pathlib

    if len(sys.argv) != 2:
        print("Usage: python evaluator.py <input_file.txt>")
        sys.exit(1)

    input_path = pathlib.Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    results = evaluate_file(str(input_path))

    output_path = input_path.parent / 'output.txt'
    print(f"Processed {len(results)} expression(s).")
    print(f"Results written to: {output_path}")