all: clean test pylint

check: clean pylint test

check-release: check documentation

release: documentation
	@(python setup.py sdist upload)

clean: clean-files reindent

clean-files:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

count:
	@(python scripts/count_loc.py)

reindent:
	@echo "running reindent.py"
	@python scripts/reindent.py -r -B .
	@echo "reindent... finished"

test:
	@nosetests
