<div align="center">
  <img src="assets/logo-smt-em-tempo.png" alt="Logo SMT em Tempo" width="230">

  # SMT em Tempo

  **Previsão da duração da troca de produto em uma linha SMT**

  Trabalho final do módulo de Machine Learning do Curso de Capacitação Tecnológica em IA e Transformação Digital.

  [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/smt_changeover_prediction.ipynb)

  [Notebook no GitHub](https://github.com/JulianaBallin/SMT-Changeover-Prediction/blob/main/smt_changeover_prediction.ipynb)

  **Entrega do trabalho final (N4):**
  [![Regressão no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/entrega_N4/N4_TrocaSMT_Aula05_Regressao.ipynb)
  [![Classificação no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/entrega_N4/N4_TrocaSMT_Aula06_Classificacao.ipynb)

  [Regressão no GitHub](https://github.com/JulianaBallin/SMT-Changeover-Prediction/blob/main/entrega_N4/N4_TrocaSMT_Aula05_Regressao.ipynb) · [Classificação no GitHub](https://github.com/JulianaBallin/SMT-Changeover-Prediction/blob/main/entrega_N4/N4_TrocaSMT_Aula06_Classificacao.ipynb)
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
| [N4_TrocaSMT_Aula05_Regressao.ipynb](entrega_N4/N4_TrocaSMT_Aula05_Regressao.ipynb) | Notebook da regressão, no modelo da disciplina (média, árvore e reta) |
| [N4_TrocaSMT_Aula06_Classificacao.ipynb](entrega_N4/N4_TrocaSMT_Aula06_Classificacao.ipynb) | Notebook da classificação, no modelo da disciplina (matriz de confusão e árvore) |
| [resultados_N4](entrega_N4/resultados_N4) | Arquivos `.json` com os resultados de cada parte |
| [N4_apresentacao.pptx](entrega_N4/N4_apresentacao.pptx) | Apresentação curta de seis slides, no roteiro de cinco minutos do enunciado |
| [N4_limpo.csv](entrega_N4/N4_limpo.csv) | Base limpa fornecida pelo professor, usada nos notebooks N4 |
| [smt_changeover_prediction.ipynb](smt_changeover_prediction.ipynb) | Notebook principal com divisão temporal, exploração, regressão, classificação e respostas às perguntas do curso |
| [apresentacao_smt_em_tempo.pptx](docs/apresentacao/apresentacao_smt_em_tempo.pptx) | Apresentação completa de quinze slides (números da base anterior) |
| [apresentacao_smt_em_tempo.pdf](docs/apresentacao/apresentacao_smt_em_tempo.pdf) | Versão em PDF da apresentação completa (números da base anterior) |
| [relatorio_tecnico_smt_em_tempo.pdf](docs/relatorio/relatorio_tecnico_smt_em_tempo.pdf) | Relatório técnico em formato A4, material bônus (números da base anterior) |
| [N4_limpo.csv](dataset/raw/N4_limpo.csv) | Base limpa do professor, lida pelo pipeline e pelo notebook principal |
| [N4_TrocaSMT.csv](dataset/raw/N4_TrocaSMT.csv) | Primeira versão da base, preservada sem alterações |
| [N4_TrocaSMT_limpo.csv](dataset/processed/N4_TrocaSMT_limpo.csv) | Base usada na análise, exportada pelo pipeline |
| [logo-smt-em-tempo.png](assets/logo-smt-em-tempo.png) | Identidade visual da linha SMT com relógio ao fundo |

## Execução no Google Colab

**Notebooks N4 (regressão e classificação):**

1. Use o botão do notebook desejado no início deste README.
2. Faça upload de `entrega_N4/N4_limpo.csv` quando solicitado.
3. Selecione **Ambiente de execução > Executar tudo**.
4. Baixe o arquivo `.json` gerado pelo painel **Arquivos**.

**Notebook principal:** ele importa o código de `src` e lê `dataset/raw/N4_limpo.csv`, então precisa do repositório completo. Clone o repositório e execute o notebook a partir da raiz, ou use o botão **Abrir no Colab** e envie essas pastas.

Os notebooks também podem ser abertos diretamente na branch principal pelos links do GitHub.

## Resultado principal

Os resultados usam a base limpa do professor e dependem de como as trocas são separadas em treino, validação e teste.

| | Notebooks N4 (sorteio 60/20/20, `random_state=42`) | Notebook principal (divisão temporal) |
| --- | --- | --- |
| Regressão (MAE no teste) | **1,93 min** (árvore de profundidade 4) | 2,12 min (árvore de profundidade 5) |
| Referência simples (MAE) | 6,10 min (média, validação) | 6,27 min (mediana, teste) |
| Classificação (recall no teste) | **87,1%** (88 de 101 trocas demoradas) | 99,0% (101 de 102) |
| Precisão e F1 no teste | 71,5% e 78,6% | 80,8% e 89,0% |

A apresentação curta e a entrega do enunciado usam os números dos notebooks N4. A meta de erro da regressão é de 3,5 minutos e foi atendida nos dois casos.

## Estrutura

A entrega do enunciado fica em `entrega_N4`: os dois notebooks, a base limpa, os `.json` e a apresentação curta. Os dados originais permanecem isolados em `dataset/raw`. Bases limpas, auditorias, divisões e previsões ficam em `dataset/processed`. Gráficos, métricas e prévias geradas ficam em `outputs`. O código necessário para reproduzir a análise permanece versionado em `src` e os geradores dos documentos ficam em `scripts`.

```text
SMT-Changeover-Prediction/
├── assets/                  # Logo e ilustrações estáticas
├── dataset/
│   ├── raw/                 # Primeira versão da base e base limpa do professor
│   └── processed/           # Bases limpas, auditorias e previsões
├── entrega_N4/              # Notebooks N4, .json, base limpa e apresentação curta
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
