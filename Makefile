# Variables
ENV_DIR = venv

.PHONY: run-format run-install

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
