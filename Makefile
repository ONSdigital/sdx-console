build:
	pipenv --three
	pipenv install --dev

test:
	pipenv run flake8 --exclude ./lib/*
