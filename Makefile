all:
	mkdir -p bin
	cp lexer.py bin/
	chmod +x bin/lexer.py
	cp parser.py bin/
	chmod +x bin/parser.py
	cp interpreter.py bin/
	chmod +x bin/interpreter.py
	cp compiler.py bin/
	chmod +x bin/compiler.py
	cp vm.py bin/
	chmod +x bin/vm.py
clean:
	-rm -rf bin