import sys
import os
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


def compile_jack_file(jack_file_path):
    jack_folder = os.path.dirname(os.path.abspath(jack_file_path))
    project_folder = os.path.dirname(jack_folder)
    output_folder = os.path.join(project_folder, 'out')

    os.makedirs(output_folder, exist_ok=True)
    module_name = os.path.splitext(os.path.basename(jack_file_path))[0]

    print(f'Compiling {jack_file_path} ...')

    tokenizer = JackTokenizer(jack_file_path, output_folder)
    tokens = tokenizer.tokenize()
    print(f'No.of Tokens: {len(tokens)}')

    engine = CompilationEngine(tokens, output_folder, module_name)
    engine.compile_class()
    engine.close()
    print(f'Written {module_name}.xml and {module_name}.vm')


def main():
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} <file.jack | directory>')
        sys.exit(1)

    source_path = sys.argv[1]

    if os.path.isdir(source_path):
        jack_files = [
            os.path.join(source_path, filename)
            for filename in os.listdir(source_path)
            if filename.endswith('.jack')
        ]
        if not jack_files:
            print(f'No .jack files found in {source_path}')
            sys.exit(1)
        for jack_file in sorted(jack_files):
            compile_jack_file(jack_file)
    elif os.path.isfile(source_path):
        compile_jack_file(source_path)
    else:
        print(f'Not found: {source_path}')
        sys.exit(1)


if __name__ == '__main__':
    main()