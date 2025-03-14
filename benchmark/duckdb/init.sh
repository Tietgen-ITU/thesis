#!/bin/bash

build_duckdb_and_install_python_client() {
	CURRENT_DIR=$(pwd)

	cd ../../nvmefs
	BUILD_PYTHON=1 GEN=ninja make release

	cd $CURRENT_DIR
}

init_environment() {
    if [ -e ".venv" ]; then
        source .venv/bin/activate
        echo "Activating environment..."
    else
        echo "Creating environment and installing dependencies..."
        python3 -m venv .venv
        source .venv/bin/activate

		build_duckdb_and_install_python_client
        pip3 install -r requirements.txt
    fi
}

init_environment
