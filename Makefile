build:
	python3 src/main.py -g

clean:
	python3 src/main.py -c

test:
	python3 src/main.py -g 1

resclear:
	rm -f results/*

default:
	python3 src/main.py -g