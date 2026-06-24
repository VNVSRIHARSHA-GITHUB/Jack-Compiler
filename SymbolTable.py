#### DA2304 Assignment 3 

## Directory layout

jack/
  Conv.jack
  Main.jack

src/
  JackTokenizer.py
  CompilationEngine.py
  SymbolTable.py
  VMWriter.py
  JackCompiler.py
  README.md

out/
  ConvT.xml
  MainT.xml
  Conv.xml
  Main.xml
  Conv.vm
  Main.vm

conv_vm.asm - single .asm file for Conv.vm and Main.vm and builtin Os vm files .

Harsha_DA24B034.pdf - report 

Requirements
Python 3.10+


## How to run

Make sure your working directory ends with \DA2304_Assignment3_DA24B034
Compile a single file

python src/JackCompiler.py jack/Conv.jack
python src/JackCompiler.py jack/Main.jack

Compile an entire directory
python src/JackCompiler.py jack/

Each .jack file produces three artefacts written to the out/ directory:
Artefact       | Description
-------------- | ---------------------------------------
<Name>T.xml    | Flat token stream (JackTokenizer.py output)
<Name>.xml     | Parse-tree XML (syntax analyser)
<Name>.vm      | VM code (code generator)
