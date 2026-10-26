SHELL := /bin/bash

PYTHON ?= python3
ENV_DIR := .venv-smt-changeover
ENV_PYTHON := $(ENV_DIR)/bin/python
ENV_JUPYTER := $(ENV_DIR)/bin/jupyter

.PHONY: menu setup analyze notebook preview report-preview slides report all test lint

menu:
	@echo "SMT em Tempo"
	@echo "1) Preparar ambiente virtual"
	@echo "2) Executar análise e gráficos"
	@echo "3) Gerar e executar notebook"
	@echo "4) Gerar slides em PPTX e PDF"
	@echo "5) Gerar relatório técnico"
	@echo "6) Gerar todos os entregáveis"
	@echo "7) Executar testes"
	@echo "8) Executar Pylint"
	@read -rp "Escolha uma opção: " option; \
	case "$$option" in \
		1) $(MAKE) setup ;; \
		2) $(MAKE) analyze ;; \
		3) $(MAKE) notebook ;; \
		4) $(MAKE) slides ;; \
		5) $(MAKE) report ;; \
		6) $(MAKE) all ;; \
		7) $(MAKE) test ;; \
		8) $(MAKE) lint ;; \
		*) echo "Opção inválida"; exit 1 ;; \
	esac

setup:
	$(PYTHON) -m venv $(ENV_DIR)
	$(ENV_PYTHON) -m pip install --upgrade pip
	$(ENV_PYTHON) -m pip install -r requirements.txt
	@echo "Ambiente pronto. Para ativar: source $(ENV_DIR)/bin/activate"

analyze:
	$(ENV_PYTHON) fontes/analise.py

notebook: analyze
	$(ENV_PYTHON) fontes/gerar_notebook.py
	$(ENV_JUPYTER) nbconvert --to notebook --execute --inplace smt_changeover_prediction.ipynb --ExecutePreprocessor.timeout=600

preview: notebook
	@tmp_dir=$$(mktemp -d /tmp/smt-notebook-XXXXXX); \
	$(ENV_JUPYTER) nbconvert --to html smt_changeover_prediction.ipynb --output notebook.html --output-dir "$$tmp_dir" >/dev/null; \
	google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=1500,1000 \
		--screenshot=assets/preview-notebook.png "file://$$tmp_dir/notebook.html" >/dev/null 2>&1

report-preview: report
	pdftoppm -png -f 1 -singlefile -r 110 docs/relatorio/relatorio_tecnico_smt_em_tempo.pdf assets/preview-relatorio >/dev/null 2>&1

slides: preview report-preview
	$(ENV_PYTHON) fontes/gerar_slides.py
	@lo_profile=$$(mktemp -d /tmp/lo-smt-slides-XXXXXX); \
	libreoffice -env:UserInstallation="file://$$lo_profile" --headless --convert-to pdf \
		--outdir docs/apresentacao docs/apresentacao/apresentacao_smt_em_tempo.pptx

report: analyze
	$(ENV_PYTHON) fontes/gerar_relatorio.py

all: slides test

test:
	$(ENV_PYTHON) -m pytest -q

lint:
	$(ENV_PYTHON) -m pylint fontes tests
