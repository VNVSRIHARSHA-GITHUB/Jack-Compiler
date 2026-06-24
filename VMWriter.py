class SymbolTable:
    def __init__(self):
        self.class_table: dict = {}
        self.sub_table: dict = {}
        self.counts = {'static': 0, 'field': 0, 'argument': 0, 'local': 0}

    def reset_subroutine_scope(self):
        """Reset the current subroutine symbol scope before compiling a new subroutine."""
        self.sub_table = {}
        self.counts['argument'] = 0
        self.counts['local'] = 0

    def define(self, name, typ, kind):
        """Register a symbol in the current scope."""
        idx = self.counts[kind]
        entry = {'type': typ, 'kind': kind, 'index': idx}
        self.counts[kind] += 1
        if kind in ('static', 'field'):
            self.class_table[name] = entry
        else:
            self.sub_table[name] = entry

    def lookup(self, name):
        if name in self.sub_table:
            return self.sub_table[name]
        if name in self.class_table:
            return self.class_table[name]
        return None

    def get_kind(self, name):
        symbol = self.lookup(name)
        return symbol['kind'] if symbol else None

    def get_type(self, name):
        symbol = self.lookup(name)
        return symbol['type'] if symbol else None

    def get_index(self, name):
        symbol = self.lookup(name)
        return symbol['index'] if symbol else None

    def count_vars(self, kind):
        return self.counts[kind]

    @staticmethod
    def segment(kind):
        return {'static': 'static', 'field': 'this',
                'argument': 'argument', 'local': 'local'}[kind]

    def dump(self):
        lines = ['___Class scope___']
        for n, e in self.class_table.items():
            lines.append(f'  {n}: {e}')
        lines.append('___Subroutine scope___')
        for n, e in self.sub_table.items():
            lines.append(f'  {n}: {e}')
        return '\n'.join(lines)