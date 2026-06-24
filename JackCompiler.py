import os
from SymbolTable import SymbolTable
from VMWriter import VMWriter

operation_map = {'+': 'add', '-': 'sub', '*': None, '/': None,
          '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'}

unary_op_map = {'-': 'neg', '~': 'not'}


class CompilationEngine:
    def __init__(self, tokens, out_dir, class_name):
        self.tokens = tokens
        self.position = 0
        self.class_name = class_name
        self.output_dir = out_dir


        xml_path = os.path.join(out_dir, class_name + '.xml')
        self.xml_file = open(xml_path, 'w')

        vm_path = os.path.join(out_dir, class_name + '.vm')
        self.vm_writer = VMWriter(vm_path)

        self.symbol_table = SymbolTable()
        self.label_counter = 0

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else ('', '')

    def advance(self):
        tok = self.tokens[self.position]
        self.position += 1
        return tok

    def eat(self, expected_val=None, expected_type=None):
        tok_type, tok_val = self.advance()
        if expected_val and tok_val != expected_val:
            raise SyntaxError(f'Expected "{expected_val}", got "{tok_val}"')
        if expected_type and tok_type != expected_type:
            raise SyntaxError(f'Expected type {expected_type}, got {tok_type}')
        return tok_type, tok_val

    def write_xml_line(self, line):
        self.xml_file.write(line + '\n')

    def write_xml_token(self, indent, tok_type, tok_val):
        from JackTokenizer import escape
        sp = '  ' * indent
        self.write_xml_line(f'{sp}<{tok_type}> {escape(tok_val)} </{tok_type}>')

    def next_label(self):
        lbl = f'L{self.label_counter}'
        self.label_counter += 1
        return lbl

    def close(self):
        self.xml_file.close()
        self.vm_writer.close()

    def compile_class(self):
        self.write_xml_line('<class>')
        self.eat_write('class', indent=1)
        _, cname = self.eat(expected_type='identifier')
        self.write_xml_token(1, 'identifier', cname)
        self.eat_write('{', indent=1)

        while self.peek()[1] in ('static', 'field'):
            self.compile_class_variable_declaration(indent=1)

        while self.peek()[1] in ('constructor', 'function', 'method'):
            self.compile_subroutine_declaration(indent=1)

        self.eat_write('}', indent=1)
        self.write_xml_line('</class>')

    def compile_class_variable_declaration(self, indent):
        self.write_xml_line('  ' * indent + '<classVarDec>')
        i = indent + 1
        _, kind = self.eat(expected_type='keyword')
        self.write_xml_token(i, 'keyword', kind)
        typ = self.compile_type(i)

        _, name = self.eat(expected_type='identifier')
        self.write_xml_token(i, 'identifier', name)
        self.symbol_table.define(name, typ, kind)
        while self.peek()[1] == ',':
            self.eat_write(',', indent=i)
            _, name = self.eat(expected_type='identifier')
            self.write_xml_token(i, 'identifier', name)
            self.symbol_table.define(name, typ, kind)
        self.eat_write(';', indent=i)
        self.write_xml_line('  ' * indent + '</classVarDec>')

    def compile_subroutine_declaration(self, indent):
        self.symbol_table.reset_subroutine_scope()
        self.write_xml_line('  ' * indent + '<subroutineDec>')
        i = indent + 1

        _, sub_kind = self.eat(expected_type='keyword')  
        self.write_xml_token(i, 'keyword', sub_kind)

        if self.peek()[1] == 'void':
            self.eat_write('void', indent=i)
            ret_type = 'void'
        else:
            ret_type = self.compile_type(i)

        _, sub_name = self.eat(expected_type='identifier')
        self.write_xml_token(i, 'identifier', sub_name)
        full_name = f'{self.class_name}.{sub_name}'

        self.eat_write('(', indent=i)

        if sub_kind == 'method':
            self.symbol_table.define('this', self.class_name, 'argument')

        self.compile_parameter_list(i)
        self.eat_write(')', indent=i)
        self.compile_subroutine_body(i, full_name, sub_kind)
        self.write_xml_line('  ' * indent + '</subroutineDec>')

    def compile_parameter_list(self, indent):
        self.write_xml_line('  ' * indent + '<parameterList>')
        i = indent + 1
        if self.peek()[1] != ')':
            typ = self.compile_type(i)
            _, name = self.eat(expected_type='identifier')
            self.write_xml_token(i, 'identifier', name)
            self.symbol_table.define(name, typ, 'argument')
            while self.peek()[1] == ',':
                self.eat_write(',', indent=i)
                typ = self.compile_type(i)
                _, name = self.eat(expected_type='identifier')
                self.write_xml_token(i, 'identifier', name)
                self.symbol_table.define(name, typ, 'argument')
        self.write_xml_line('  ' * indent + '</parameterList>')

    def compile_subroutine_body(self, indent, full_name, sub_kind):
        self.write_xml_line('  ' * indent + '<subroutineBody>')
        i = indent + 1
        self.eat_write('{', indent=i)
        while self.peek()[1] == 'var':
            self.compile_variable_declaration(i)
        n_locals = self.symbol_table.count_vars('local')
        self.vm_writer.write_function(full_name, n_locals)

        if sub_kind == 'constructor':
            n_fields = self.symbol_table.count_vars('field')
            self.vm_writer.write_push('constant', n_fields)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('pointer', 0)
        elif sub_kind == 'method':
            self.vm_writer.write_push('argument', 0)
            self.vm_writer.write_pop('pointer', 0)

        self.compile_statements(i)
        self.eat_write('}', indent=i)
        self.write_xml_line('  ' * indent + '</subroutineBody>')

    def compile_variable_declaration(self, indent):
        self.write_xml_line('  ' * indent + '<varDec>')
        i = indent + 1
        self.eat_write('var', indent=i)
        typ = self.compile_type(i)
        _, name = self.eat(expected_type='identifier')
        self.write_xml_token(i, 'identifier', name)
        self.symbol_table.define(name, typ, 'local')
        while self.peek()[1] == ',':
            self.eat_write(',', indent=i)
            _, name = self.eat(expected_type='identifier')
            self.write_xml_token(i, 'identifier', name)
            self.symbol_table.define(name, typ, 'local')
        self.eat_write(';', indent=i)
        self.write_xml_line('  ' * indent + '</varDec>')

    def compile_statements(self, indent):
        self.write_xml_line('  ' * indent + '<statements>')
        dispatch = {
            'let': self.compile_let,
            'if': self.compile_if,
            'while': self.compile_while,
            'do': self.compile_do,
            'return': self.compile_return,
        }
        while self.peek()[1] in dispatch:
            dispatch[self.peek()[1]](indent + 1)
        self.write_xml_line('  ' * indent + '</statements>')

    def compile_let(self, indent):
        self.write_xml_line('  ' * indent + '<letStatement>')
        i = indent + 1
        self.eat_write('let', indent=i)
        _, name = self.eat(expected_type='identifier')
        self.write_xml_token(i, 'identifier', name)

        is_array = self.peek()[1] == '['
        if is_array:
            self.push_name(name)
            self.eat_write('[', indent=i)
            self.compile_expression(i)
            self.eat_write(']', indent=i)
            self.vm_writer.write_arithmetic('add') 

        self.eat_write('=', indent=i)
        self.compile_expression(i)
        self.eat_write(';', indent=i)

        if is_array:
            self.vm_writer.write_pop('temp', 0)
            self.vm_writer.write_pop('pointer', 1)
            self.vm_writer.write_push('temp', 0)
            self.vm_writer.write_pop('that', 0)
        else:
            kind = self.symbol_table.get_kind(name)
            idx = self.symbol_table.get_index(name)
            self.vm_writer.write_pop(SymbolTable.segment(kind), idx)

        self.write_xml_line('  ' * indent + '</letStatement>')

    def compile_if(self, indent):
        self.write_xml_line('  ' * indent + '<ifStatement>')
        i = indent + 1
        lbl_else = self.next_label()
        lbl_end = self.next_label()

        self.eat_write('if', indent=i)
        self.eat_write('(', indent=i)
        self.compile_expression(i)
        self.eat_write(')', indent=i)
        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(lbl_else)

        self.eat_write('{', indent=i)
        self.compile_statements(i)
        self.eat_write('}', indent=i)
        self.vm_writer.write_goto(lbl_end)
        self.vm_writer.write_label(lbl_else)

        if self.peek()[1] == 'else':
            self.eat_write('else', indent=i)
            self.eat_write('{', indent=i)
            self.compile_statements(i)
            self.eat_write('}', indent=i)

        self.vm_writer.write_label(lbl_end)
        self.write_xml_line('  ' * indent + '</ifStatement>')

    def compile_while(self, indent):
        self.write_xml_line('  ' * indent + '<whileStatement>')
        i = indent + 1
        lbl_top = self.next_label()
        lbl_end = self.next_label()
        self.vm_writer.write_label(lbl_top)

        self.eat_write('while', indent=i)
        self.eat_write('(', indent=i)
        self.compile_expression(i)
        self.eat_write(')', indent=i)
        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(lbl_end)

        self.eat_write('{', indent=i)
        self.compile_statements(i)
        self.eat_write('}', indent=i)
        self.vm_writer.write_goto(lbl_top)
        self.vm_writer.write_label(lbl_end)
        self.write_xml_line('  ' * indent + '</whileStatement>')

    def compile_do(self, indent):
        self.write_xml_line('  ' * indent + '<doStatement>')
        i = indent + 1
        self.eat_write('do', indent=i)
        self.compile_subroutine_call(i)
        self.eat_write(';', indent=i)
        self.vm_writer.write_pop('temp', 0)
        self.write_xml_line('  ' * indent + '</doStatement>')

    def compile_return(self, indent):
        self.write_xml_line('  ' * indent + '<returnStatement>')
        i = indent + 1
        self.eat_write('return', indent=i)
        if self.peek()[1] != ';':
            self.compile_expression(i)
        else:
            self.vm_writer.write_push('constant', 0)  
        self.eat_write(';', indent=i)
        self.vm_writer.write_return()
        self.write_xml_line('  ' * indent + '</returnStatement>')

    def compile_expression(self, indent):
        self.write_xml_line('  ' * indent + '<expression>')
        i = indent + 1
        self.compile_term(i)
        while self.peek()[1] in operation_map:
            _, op = self.eat(expected_type='symbol')
            self.write_xml_token(i, 'symbol', op)
            self.compile_term(i)
            if op == '*':
                self.vm_writer.write_call('Math.multiply', 2)
            elif op == '/':
                self.vm_writer.write_call('Math.divide', 2)
            else:
                self.vm_writer.write_arithmetic(operation_map[op])
        self.write_xml_line('  ' * indent + '</expression>')

    def compile_term(self, indent):
        self.write_xml_line('  ' * indent + '<term>')
        i = indent + 1
        tok_type, tok_val = self.peek()

        if tok_type == 'integerConstant':
            self.advance()
            self.write_xml_token(i, 'integerConstant', tok_val)
            self.vm_writer.write_push('constant', int(tok_val))

        elif tok_type == 'stringConstant':
            self.advance()
            self.write_xml_token(i, 'stringConstant', tok_val)
            self.vm_writer.write_push('constant', len(tok_val))
            self.vm_writer.write_call('String.new', 1)
            for ch in tok_val:
                self.vm_writer.write_push('constant', ord(ch))
                self.vm_writer.write_call('String.appendChar', 2)

        elif tok_val in ('true', 'false', 'null', 'this'):
            self.advance()
            self.write_xml_token(i, 'keyword', tok_val)
            if tok_val == 'true':
                self.vm_writer.write_push('constant', 0)
                self.vm_writer.write_arithmetic('not')
            elif tok_val in ('false', 'null'):
                self.vm_writer.write_push('constant', 0)
            else:
                self.vm_writer.write_push('pointer', 0)

        elif tok_val == '(':
            self.eat_write('(', indent=i)
            self.compile_expression(i)
            self.eat_write(')', indent=i)

        elif tok_val in ('-', '~'):
            self.advance()
            self.write_xml_token(i, 'symbol', tok_val)
            self.compile_term(i)
            self.vm_writer.write_arithmetic(unary_op_map[tok_val])

        elif tok_type == 'identifier':
            next_val = self.tokens[self.position + 1][1] if self.position + 1 < len(self.tokens) else ''
            if next_val == '[':
                _, name = self.advance()
                self.write_xml_token(i, 'identifier', name)
                self.push_name(name)
                self.eat_write('[', indent=i)
                self.compile_expression(i)
                self.eat_write(']', indent=i)
                self.vm_writer.write_arithmetic('add')
                self.vm_writer.write_pop('pointer', 1)
                self.vm_writer.write_push('that', 0)
            elif next_val in ('.', '('):
                self.compile_subroutine_call(i)
            else:
                _, name = self.advance()
                self.write_xml_token(i, 'identifier', name)
                self.push_name(name)

        self.write_xml_line('  ' * indent + '</term>')

    def compile_expression_list(self, indent):
        self.write_xml_line('  ' * indent + '<expressionList>')
        n = 0
        if self.peek()[1] != ')':
            self.compile_expression(indent + 1)
            n += 1
            while self.peek()[1] == ',':
                self.eat_write(',', indent=indent + 1)
                self.compile_expression(indent + 1)
                n += 1
        self.write_xml_line('  ' * indent + '</expressionList>')
        return n

    def compile_subroutine_call(self, indent):
        _, name = self.eat(expected_type='identifier')
        self.write_xml_token(indent, 'identifier', name)

        if self.peek()[1] == '.':
            self.eat_write('.', indent=indent)
            _, method_name = self.eat(expected_type='identifier')
            self.write_xml_token(indent, 'identifier', method_name)
            self.eat_write('(', indent=indent)

            kind = self.symbol_table.get_kind(name)
            if kind is not None:
                obj_type = self.symbol_table.get_type(name)
                self.push_name(name)
                n_args = self.compile_expression_list(indent) + 1
                full = f'{obj_type}.{method_name}'
            else:
                n_args = self.compile_expression_list(indent)
                full = f'{name}.{method_name}'

            self.eat_write(')', indent=indent)
            self.vm_writer.write_call(full, n_args)

        else:
            self.eat_write('(', indent=indent)
            self.vm_writer.write_push('pointer', 0)
            n_args = self.compile_expression_list(indent) + 1
            self.eat_write(')', indent=indent)
            self.vm_writer.write_call(f'{self.class_name}.{name}', n_args)

    def compile_type(self, indent):
        tok_type, tok_val = self.peek()
        self.advance()
        if tok_type == 'keyword':
            self.write_xml_token(indent, 'keyword', tok_val)
        else:
            self.write_xml_token(indent, 'identifier', tok_val)
        return tok_val

    def eat_write(self, val, indent):
        tok_type, tok_val = self.eat(expected_val=val)
        self.write_xml_token(indent, tok_type, tok_val)

    def push_name(self, name):
        kind = self.symbol_table.get_kind(name)
        idx = self.symbol_table.get_index(name)
        if kind is None:
            raise NameError(f'Undefined symbol: {name}')
        self.vm_writer.write_push(SymbolTable.segment(kind), idx)