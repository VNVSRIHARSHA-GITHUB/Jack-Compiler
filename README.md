import re
import os

keywords = {
    'class', 'constructor', 'function', 'method', 'field', 'static',
    'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
    'this', 'let', 'do', 'if', 'else', 'while', 'return'
}

symbols = set('{}()[].,;+-*/&|<>=~')

patterns = re.compile(
    r'//[^\n]*'                          # single line comment
    r'|/\*.*?\*/'                        # block comment
    r'|"[^"\n]*"'                        # string constant
    r'|(\d+)'                            # integer constant
    r'|([A-Za-z_]\w*)'                   # keyword or identifier
    r'|([{}()\[\].,;+\-*/&|<>=~])'      # symbol
    , re.DOTALL
)


def strip_comments(source):
    result = []
    i = 0
    n = len(source)
    while i < n:
        #Not to remove information after "//" or "/*" or "/**" if they are inside a string constant
        if source[i] == '"':
            j = i + 1
            while j < n and source[j] != '"':
                j += 1
            result.append(source[i:j+1])
            i = j + 1
        elif source[i:i+2] in ('/*', '**'):
            end = source.find('*/', i + 2)
            if end == -1:
                break
            i = end + 2
        elif source[i:i+2] == '//':
            end = source.find('\n', i)
            i = end + 1 if end != -1 else n
        else:
            result.append(source[i])
            i += 1
    return ''.join(result)


def escape(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text


class JackTokenizer:
    def __init__(self, input_path, output_dir=None):
        self.input_path = input_path
        self.output_dir = output_dir if output_dir else os.path.dirname(input_path)
        self.tokens = []
        self.class_name = os.path.splitext(os.path.basename(input_path))[0]

    def tokenize(self) :
        with open(self.input_path, 'r') as f:
            source = f.read()

        clean = strip_comments(source)
        self.tokens = []

        for m in patterns.finditer(clean):
            raw = m.group(0).strip()
            if not raw:
                continue
            if raw.startswith('"'):
                self.tokens.append(('stringConstant', raw[1:-1]))
            elif raw[0].isdigit():
                self.tokens.append(('integerConstant', raw))
            elif raw in keywords :
                self.tokens.append(('keyword', raw))
            elif raw in symbols :
                self.tokens.append(('symbol', raw))
            elif re.match(r'^[A-Za-z_]\w*$', raw):
                self.tokens.append(('identifier', raw))

        self.write_tokens_xml()
        return self.tokens

    def write_tokens_xml(self):
        out_path = os.path.join(
            self.output_dir,
            self.class_name + 'T.xml'
        )
        lines = ['<tokens>']
        for tok_type, tok_val in self.tokens:
            lines.append(f'  <{tok_type}> {escape(tok_val)} </{tok_type}>')
        lines.append('</tokens>')
        with open(out_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

if __name__ == '__main__':
    import sys
    t = JackTokenizer(sys.argv[1])
    tokens = t.tokenize()