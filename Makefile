# Variables
ENV_DIR = venv

.PHONY: run-format run-install run-server run-test

run-format:
	black .

run-install:
	if [ ! -d "${ENV_DIR}" ]; then \
		echo "Creating a new virtual environment ${ENV_DIR}..."; \
		python3.12 -m venv ${ENV_DIR}; \
		pip install --upgrade pip; \
	fi

	echo "Setting up virtual environment..."; \
	source ${ENV_DIR}/bin/activate && pip install -r requirements.txt

run-server:
	./start-server.sh

run-test:
	coverage run -m pytest
	coverage report -m

run-linter:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
