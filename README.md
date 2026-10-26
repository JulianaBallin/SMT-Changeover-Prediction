<div align="center">
  <img src="assets/logo-smt-em-tempo.png" alt="Logo SMT em Tempo" width="230">

  # SMT em Tempo

  **Previsão da duração da troca de produto em uma linha SMT**

  Trabalho final do módulo de Machine Learning do Curso de Capacitação Tecnológica em IA e Transformação Digital.

  [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/smt_changeover_prediction.ipynb)

  [Notebook no GitHub](https://github.com/JulianaBallin/SMT-Changeover-Prediction/blob/main/smt_changeover_prediction.ipynb)
</div>

---

## Objetivo

Apoiar o supervisor na escolha das trocas de produto que devem receber ajuda adicional antes de a linha parar. O projeto usa informações disponíveis no planejamento para responder duas perguntas:

1. Quantos minutos a troca deve levar?
2. A troca deve ultrapassar 42 minutos?

Os dados são sintéticos e foram preparados para a atividade do curso.

Equipe:

- Juliana Ballin Lima
- Fernanda de Oliveira da Costa
- Pedro Henrique Oliveira Dias

## Entregáveis

| Arquivo | Finalidade |
| --- | --- |
| [smt_changeover_prediction.ipynb](smt_changeover_prediction.ipynb) | Notebook executado com limpeza, exploração, regressão e classificação |
| [apresentacao_smt_em_tempo.pptx](docs/apresentacao/apresentacao_smt_em_tempo.pptx) | Apresentação editável de onze slides |
| [apresentacao_smt_em_tempo.pdf](docs/apresentacao/apresentacao_smt_em_tempo.pdf) | Versão da apresentação para visualização e compartilhamento |
| [relatorio_tecnico_smt_em_tempo.pdf](docs/relatorio/relatorio_tecnico_smt_em_tempo.pdf) | Relatório técnico detalhado em formato A4, material bônus |
| [N4_TrocaSMT.csv](dataset/raw/N4_TrocaSMT.csv) | Base original preservada sem alterações |
| [N4_TrocaSMT_limpo.csv](dataset/processed/N4_TrocaSMT_limpo.csv) | Base resultante do pipeline reproduzível |
| [logo-smt-em-tempo.png](assets/logo-smt-em-tempo.png) | Identidade visual da linha SMT com relógio ao fundo |

## Execução no Google Colab

1. Use o botão **Abrir no Colab** no início deste README.
2. Faça upload do CSV bruto disponível em `dataset/raw/N4_TrocaSMT.csv` quando solicitado.
3. Selecione **Ambiente de execução > Executar tudo**.
4. Consulte as métricas finais e os arquivos exportados na última célula.

O notebook também pode ser aberto diretamente na branch principal pelo link **Notebook no GitHub**.

## Resultado principal

A árvore de regressão alcançou MAE de 2,66 minutos, redução de 67,4% frente à referência simples. Na classificação, o modelo encontrou 89 das 102 trocas demoradas do teste, com recall de 87,3%, 13 casos perdidos e 31 falsos alarmes.

## Estrutura

Os dados originais permanecem isolados em `dataset/raw`. Bases limpas, auditorias, divisões e previsões ficam em `dataset/processed`. Gráficos, métricas e prévias geradas ficam em `outputs`. O código necessário para reproduzir a análise permanece versionado em `src` e os geradores dos documentos ficam em `scripts`.

```text
SMT-Changeover-Prediction/
├── assets/                  # Logo e ilustrações estáticas
├── dataset/
│   ├── raw/                 # Base original preservada
│   └── processed/           # Bases limpas, auditorias e previsões
├── docs/
│   ├── apresentacao/        # Slides editáveis e PDF
│   └── relatorio/           # Relatório técnico bônus
├── outputs/
│   ├── charts/              # Gráficos produzidos pela análise
│   ├── metrics/             # Resumo das métricas finais
│   └── previews/            # Prévias usadas na apresentação
├── scripts/                 # Geração do notebook e dos documentos
├── src/smt_changeover/      # Pipeline reproduzível de análise
├── tests/                   # Testes do contrato analítico
└── smt_changeover_prediction.ipynb
```

## Regeneração local

A regeneração exige Python 3.12 ou compatível, LibreOffice, Google Chrome ou Chromium e as dependências de [requirements.txt](requirements.txt).

```bash
make menu
```

O alvo `make setup` cria o ambiente `.venv-smt-changeover`. O alvo `make all` reconstrói a base limpa, os gráficos, o notebook executado, os slides e o relatório bônus.

## Repositório

[github.com/JulianaBallin/SMT-Changeover-Prediction](https://github.com/JulianaBallin/SMT-Changeover-Prediction)

O botão no início deste README abre o notebook da branch principal diretamente no Google Colab.
