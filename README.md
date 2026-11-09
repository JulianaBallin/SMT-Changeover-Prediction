<div align="center">
  <img src="assets/logo-smt-em-tempo.png" alt="Logo SMT em Tempo" width="230">

  # SMT em Tempo

  **Previsão da duração da troca de produto em uma linha SMT**

  Trabalho final do módulo de Machine Learning do Curso de Capacitação Tecnológica em IA e Transformação Digital.

  [![Regressão no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/notebooks/N4_TrocaSMT_Aula05_Regressao.ipynb)
  [![Classificação no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JulianaBallin/SMT-Changeover-Prediction/blob/main/notebooks/N4_TrocaSMT_Aula06_Classificacao.ipynb)
</div>

---

<div align="center">

## Objetivo

</div>

Apoiar o supervisor na escolha das trocas de produto que devem receber ajuda adicional antes de a linha parar. O projeto usa informações disponíveis no planejamento para responder duas perguntas:

1. Quantos minutos a troca deve levar?
2. A troca deve ultrapassar 42 minutos?

Os dados são sintéticos e foram preparados para a atividade do curso.

Equipe:

- Juliana Ballin Lima
- Fernanda de Oliveira da Costa
- Pedro Henrique Oliveira Dias

---

<div align="center">

## Notebooks entregáveis

</div>

Os únicos cadernos entregáveis são os dois notebooks abaixo. Ambos usam a base oficial `N4_limpo.csv` e estão executados com os resultados finais.

| Notebook | Pergunta | Resultado principal |
| --- | --- | --- |
| [N4_TrocaSMT_Aula05_Regressao.ipynb](notebooks/N4_TrocaSMT_Aula05_Regressao.ipynb) | Quantos minutos a troca vai levar? | Árvore de profundidade 4, MAE de 1,93 min no teste |
| [N4_TrocaSMT_Aula06_Classificacao.ipynb](notebooks/N4_TrocaSMT_Aula06_Classificacao.ipynb) | A troca vai passar de 42 minutos? | Recall de 87,1% e F1 de 78,6% no teste |

### Arquivos da entrega

| Arquivo | Finalidade |
| --- | --- |
| [N4_regressao.json](outputs/metrics/N4_regressao.json) | Resultados reproduzíveis da regressão |
| [N4_classificacao.json](outputs/metrics/N4_classificacao.json) | Resultados reproduzíveis da classificação |
| [apresentacao_smt_em_tempo.pptx](docs/apresentacao/apresentacao_smt_em_tempo.pptx) | Apresentação editável de sete slides para cinco minutos |
| [apresentacao_smt_em_tempo.pdf](docs/apresentacao/apresentacao_smt_em_tempo.pdf) | Versão final da apresentação em PDF |
| [relatorio_tecnico_smt_em_tempo.pdf](docs/relatorio/relatorio_tecnico_smt_em_tempo.pdf) | Relatório técnico complementar com análise temporal |

---

<div align="center">

## Resultados

</div>

Os números abaixo vêm dos dois notebooks, com sorteio 60/20/20 e `random_state=42`.

| Etapa | Validação | Teste |
| --- | ---: | ---: |
| Regressão, MAE da árvore | 2,04 min | **1,93 min** |
| Regressão, referência pela média | 6,10 min | Não aplicada |
| Classificação, recall | 93,1% | **87,1%** |
| Classificação, precisão | 78,5% | **71,5%** |
| Classificação, F1 | 85,2% | **78,6%** |

A regressão atende à meta de MAE de até 3,5 minutos. Na classificação, a árvore encontrou 88 de 101 trocas demoradas no teste, com 13 falsos negativos e 35 falsos positivos.

---

<div align="center">

## Apresentação de cinco minutos

</div>

A apresentação usa o template institucional Cyber Labs e resume os dois notebooks em sete slides. Ela inclui:

- o problema e as duas perguntas de negócio;
- o gráfico de profundidade extraído do notebook de regressão;
- a matriz de confusão extraída do notebook de classificação;
- os desafios de dados ausentes, sobreajuste e queda entre validação e teste;
- curiosidades sobre mudança de família, linha SMT e características mais úteis;
- respostas às oito perguntas gerais do curso;
- decisão apoiada e limites do estudo.

---

<div align="center">

## Execução no Google Colab

</div>

1. Abra um dos notebooks pelos botões no início deste README.
2. Baixe a [base oficial N4_limpo.csv](dataset/raw/N4_limpo.csv).
3. Faça o upload do arquivo quando o notebook solicitar.
4. Execute as células de cima para baixo.
5. Baixe o JSON gerado pelo painel **Arquivos** do Colab.

O conjunto de teste deve ser aberto apenas uma vez, depois de todas as escolhas feitas com a validação.

---

<div align="center">

## Estrutura do projeto

</div>

```text
SMT-Changeover-Prediction/
├── assets/                       # Identidade visual e ilustrações
├── dataset/
│   ├── raw/                      # Bases recebidas sem duplicação
│   └── processed/                # Tabelas auxiliares da análise
├── docs/
│   ├── apresentacao/             # Apresentação final em PPTX e PDF
│   └── relatorio/                # Relatório técnico em PDF
├── notebooks/                    # Os dois notebooks entregáveis
├── outputs/
│   ├── charts/                   # Gráficos produzidos pela análise
│   └── metrics/                  # JSONs e métricas finais
├── src/smt_changeover/           # Pipeline reproduzível de análise
└── tests/                        # Testes do contrato analítico
```

---

<div align="center">

## Repositório

[github.com/JulianaBallin/SMT-Changeover-Prediction](https://github.com/JulianaBallin/SMT-Changeover-Prediction)

</div>
