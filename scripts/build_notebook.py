"""Build the final project notebook with concise code and explanatory text."""

# pylint: disable=line-too-long

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_DIR / "smt_changeover_prediction.ipynb"


def markdown(text: str):
    """Create one normalized Markdown cell."""
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text: str):
    """Create one normalized code cell."""
    return nbf.v4.new_code_cell(dedent(text).strip())


def build_notebook() -> None:
    """Write the final notebook to the project root."""
    notebook = nbf.v4.new_notebook()
    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    }
    notebook["cells"] = [
        markdown(
            """
            # SMT em Tempo
            ## Previsão da duração da troca de produto na linha SMT

            **Projeto 4 - Trabalho final de Machine Learning**

            **Equipe:** Juliana Ballin Lima, Fernanda de Oliveira da Costa e Pedro Henrique Oliveira Dias

            Este notebook investiga quais trocas precisam de atenção antes de começar. A análise responde duas perguntas:

            1. Quantos minutos a troca deve levar?
            2. A troca deve ultrapassar 42 minutos?

            Os dados são sintéticos e foram preparados para o curso.
            """
        ),
        markdown(
            """
            ## 1. Como a análise foi organizada

            Seguimos o ciclo usado nas aulas:

            **observar → decidir → corrigir → conferir → dividir no tempo → treinar → avaliar**

            O conjunto de teste fica reservado até o final. Assim, ele simula trocas futuras que o modelo ainda não viu.
            """
        ),
        code(
            """
            from pathlib import Path
            import json
            import os
            import subprocess
            import sys
            import pandas as pd
            from IPython.display import Image, display

            # No Google Colab, baixa o repositório para ter as pastas src e dataset.
            try:
                import google.colab  # noqa: F401
                EM_COLAB = True
            except ImportError:
                EM_COLAB = False
            if EM_COLAB and not Path("src/smt_changeover").exists():
                subprocess.run(
                    ["git", "clone", "--depth", "1",
                     "https://github.com/JulianaBallin/SMT-Changeover-Prediction.git"],
                    check=True,
                )
                os.chdir("SMT-Changeover-Prediction")

            PROJECT_DIR = Path.cwd()
            SRC_DIR = PROJECT_DIR / "src"
            if str(SRC_DIR) not in sys.path:
                sys.path.insert(0, str(SRC_DIR))

            from smt_changeover.analysis import (
                CATEGORICAL_FEATURES,
                FEATURES,
                NUMERIC_FEATURES,
                generate_charts,
                load_clean_data,
                save_outputs,
                temporal_split,
                train_and_evaluate,
            )

            pd.set_option("display.max_columns", 30)
            pd.set_option("display.precision", 3)
            print("Pasta do projeto:", PROJECT_DIR)
            """
        ),
        markdown(
            """
            ## 2. Abrir e compreender o dataset

            Cada linha representa uma troca de produto. As oito entradas abaixo existem antes da troca e podem apoiar a previsão.

            | Entrada | Significado |
            |---|---|
            | `alimentadores_a_trocar` | carretéis que precisam ser substituídos |
            | `kit_preparado_pct` | percentual do kit já separado |
            | `experiencia_operador_meses` | experiência do operador |
            | `componentes_novos` | componentes ainda não usados pela linha |
            | `tamanho_lote_placas` | placas previstas no lote seguinte |
            | `linha_smt` | linha SMT1, SMT2 ou SMT3 |
            | `muda_familia` | indica mudança de família de produto |
            | `turno` | manhã, tarde ou noite |

            `tempo_troca_min` é o alvo da regressão. `troca_demorada` é o alvo da classificação. `atraso_no_plano_min` só existe depois do fato e não entra nos modelos.
            """
        ),
        code(
            """
            # Carrega a base limpa fornecida pelo professor (N4_limpo.csv), sem alterá-la.
            dados, registro_limpeza, suspeitas, qualidade = load_clean_data()
            print("Dimensão recebida:", dados.shape)
            display(dados.head(6))
            """
        ),
        markdown(
            """
            ## 3. Base limpa e conferências

            Usamos a base **já limpa** fornecida pelo professor (`N4_limpo.csv`, limpeza da Aula 3). Nela, as duplicatas exatas já foram removidas, as grafias e os formatos foram padronizados, os códigos `9999` e as medidas fora dos critérios didáticos viraram ausentes no campo afetado, e os alvos não foram preenchidos.

            Por isso, aqui não refazemos a limpeza: conferimos que a base chegou consistente.
            """
        ),
        code(
            """
            # Confere a consistência da base recebida.
            print("Trocas na base:", len(dados))
            print("Linhas duplicadas:", int(dados.duplicated().sum()))
            print("Período:", dados["data_operacao"].min().date(), "a", dados["data_operacao"].max().date())
            regra_42 = dados["tempo_troca_min"].gt(42).astype(int).eq(dados["troca_demorada"]).all()
            print("Classe confere com a regra de 42 minutos:", bool(regra_42))
            """
        ),
        markdown(
            """
            ### O que continuou ausente

            Ausência não significa zero. O preenchimento das entradas numéricas será feito pela mediana aprendida somente no treino. Categorias ausentes, se surgirem, serão tratadas pelo pipeline.
            """
        ),
        code(
            """
            display(qualidade)
            print("Trocas preservadas com ao menos uma entrada ausente:",
                  int(dados[FEATURES].isna().any(axis=1).sum()))
            print("Alvos numéricos ausentes:", int(dados["tempo_troca_min"].isna().sum()))
            print("Classes ausentes:", int(dados["troca_demorada"].isna().sum()))
            """
        ),
        markdown(
            """
            ## 4. Divisão temporal

            A previsão será usada em trocas futuras. Por isso, as datas mais antigas formam o treino, o período seguinte orienta a escolha dos modelos e as datas mais recentes formam o teste final. Um mesmo dia não aparece em duas divisões.
            """
        ),
        code(
            """
            # Separa passado, período de escolha e futuro.
            divisao, fim_treino, fim_validacao = temporal_split(dados)
            resumo_divisoes = (
                pd.DataFrame({"data": dados["data_operacao"], "divisao": divisao})
                .groupby("divisao")
                .agg(registros=("data", "size"), inicio=("data", "min"), fim=("data", "max"))
            )
            display(resumo_divisoes)
            """
        ),
        markdown(
            """
            ### Como cada divisão é usada

            - **Treino:** aprende as regras dos modelos.
            - **Validação:** escolhe o modelo e a profundidade.
            - **Teste:** mede o resultado final em dados mais recentes.

            O teste não participa das escolhas.
            """
        ),
        markdown(
            """
            ## 5. Exploração somente no treino

            A classe 1 significa tempo acima de 42 minutos. O limite define o problema operacional e não um erro de dados.
            """
        ),
        code(
            """
            # Explora apenas o treino para não antecipar o futuro.
            treino = dados.loc[divisao.eq("treino")]
            distribuicao = treino["troca_demorada"].value_counts().sort_index().to_frame("Registros")
            distribuicao["Porcentagem"] = 100 * distribuicao["Registros"] / len(treino)
            distribuicao.index = ["Até 42 min", "Acima de 42 min"]
            display(distribuicao.round(1))
            """
        ),
        code(
            """
            display(Image(filename="outputs/charts/01_distribuicao_tempo.png", width=850))
            """
        ),
        markdown(
            """
            A maioria das trocas fica abaixo do limite, mas a classe demorada ainda representa cerca de um quarto da base. A mediana é mais adequada que a média para preencher entradas porque é menos sensível aos valores extremos documentados.
            """
        ),
        code(
            """
            display(Image(filename="outputs/charts/02_relacoes_principais.png", width=980))
            display(Image(filename="outputs/charts/03_risco_por_kit_e_familia.png", width=900))
            """
        ),
        markdown(
            """
            ### Leitura exploratória

            - Maior preparação do kit aparece associada a tempos menores.
            - Mais alimentadores a trocar aparece associado a tempos maiores.
            - Mudar de família eleva o risco principalmente quando o kit está pouco preparado.

            Essas relações orientam a interpretação, mas não provam causalidade.
            """
        ),
        markdown(
            """
            ## 6. Preparo e prevenção de vazamento

            O pipeline aplica a mesma regra a todos os modelos:

            - mediana para entradas numéricas ausentes;
            - codificação `one-hot` para categorias;
            - regras aprendidas apenas na parcela usada para treinar;
            - exclusão de ID, datas, alvos e `atraso_no_plano_min`.

            A coluna posterior ao evento foi preservada no arquivo limpo para rastreabilidade, mas nunca participa da previsão.
            """
        ),
        code(
            """
            # Confere quais colunas entram no pipeline.
            print("Entradas do modelo:")
            for coluna in FEATURES:
                print("-", coluna)
            print("\\nFora das entradas: id, datas, alvos e atraso_no_plano_min")
            """
        ),
        markdown(
            """
            ## 7. Regressão: prever quantos minutos

            Comparamos três ideias: a mediana do treino como referência, uma regressão linear e árvores com profundidades de 2 a 10. A profundidade é escolhida pelo menor MAE na validação. Depois, o modelo escolhido é treinado novamente com treino e validação e avaliado uma vez no teste.
            """
        ),
        code(
            """
            # Treina no treino e compara os candidatos na validação.
            resultados = train_and_evaluate(dados, divisao)
            """
        ),
        markdown(
            """
            ### 7.1 Escolha na validação

            Menor MAE indica menor erro médio. O teste continua reservado.
            """
        ),
        code(
            """
            # Mostra os candidatos ordenados pelo MAE.
            display(resultados["regression_validation"].head(6).round(3))
            """
        ),
        markdown(
            """
            ### 7.2 Conferência no teste

            Após a escolha, treino e validação são reunidos. O teste mede o resultado final.
            """
        ),
        code(
            """
            # Compara o modelo escolhido com referências no teste.
            display(resultados["regression_test"].round(3))
            """
        ),
        code(
            """
            display(Image(filename="outputs/charts/04_comparacao_regressao.png", width=850))
            display(Image(filename="outputs/charts/05_previsto_vs_observado.png", width=620))
            """
        ),
        markdown(
            """
            ### Resultado da regressão

            A árvore de profundidade 5 alcançou MAE de **2,12 minutos** no teste. A referência simples errou **6,27 minutos** em média. A redução do erro foi de **66,2%**, com R² de **0,886**.

            O ganho mostra que as entradas conhecidas antes da troca carregam informação útil. O erro não desaparece, então a previsão deve apoiar o supervisor e não substituir sua avaliação.
            """
        ),
        markdown(
            """
            ## 8. Classificação: prever risco acima de 42 minutos

            A referência prevê sempre a classe mais comum. Também comparamos regressão logística e árvores de profundidade 2 a 10. Como perder uma troca demorada pode deixar a linha sem apoio, observamos `recall`, mas escolhemos a árvore pelo melhor F1 na validação para equilibrar casos encontrados e falsos alarmes.
            """
        ),
        markdown(
            """
            ### 8.1 Escolha na validação

            F1 equilibra trocas encontradas e alarmes incorretos. Recall mostra quantas trocas demoradas foram localizadas.
            """
        ),
        code(
            """
            colunas = ["Modelo", "Acurácia", "Precisão", "Recall", "F1", "AP", "FP", "FN", "VP"]
            # Ordena os candidatos pelo resultado de validação.
            display(resultados["classification_validation"][colunas].head(6).round(3))
            """
        ),
        markdown(
            """
            ### 8.2 Conferência no teste

            O teste mostra quantos casos futuros foram encontrados, perdidos ou sinalizados por engano.
            """
        ),
        code(
            """
            # Exibe as métricas finais sem refazer a escolha.
            display(resultados["classification_test"][colunas].round(3))
            """
        ),
        code(
            """
            display(Image(filename="outputs/charts/06_matriz_confusao.png", width=620))
            display(Image(filename="outputs/charts/07_importancia_caracteristicas.png", width=760))
            """
        ),
        markdown(
            """
            ### Resultado da classificação

            No teste, a árvore de profundidade 3:

            - encontrou **101 de 102** trocas demoradas;
            - deixou passar **1** troca demorada;
            - gerou **24** falsos alarmes;
            - alcançou `recall` de **99,0%**, precisão de **80,8%** e F1 de **89,0%**.

            A referência da classe majoritária não encontrou nenhuma troca demorada. O classificador, portanto, oferece um sinal operacional útil.
            """
        ),
        markdown(
            """
            ## 9. Como usar a previsão

            Antes de cada troca, o sistema pode ordenar os casos pela probabilidade de ultrapassar 42 minutos. O supervisor direciona primeiro o apoio disponível para os maiores riscos e mantém sua decisão humana.

            Uma política inicial pode usar o limite padrão de 50% e acompanhar três números por período:

            1. trocas demoradas encontradas;
            2. trocas demoradas perdidas;
            3. falsos alarmes que consumiram atenção.

            Se a prioridade for perder menos casos, o limite pode ser reduzido, aceitando mais falsos alarmes.
            """
        ),
        markdown(
            """
            ## 10. Limitações e aprendizados

            - A base é sintética e não demonstra desempenho numa fábrica real.
            - Associação entre kit preparado e duração não prova causa.
            - Mudanças no processo, equipe ou produto podem reduzir o desempenho ao longo do tempo.
            - O resultado precisa ser validado em operação antes de orientar recursos reais.
            - Separar por tempo produz uma avaliação mais próxima do uso futuro.
            - Uma referência simples é indispensável para saber se o modelo acrescenta valor.
            - Vazamento de dados pode criar um resultado excelente e inútil.
            """
        ),
        markdown(
            """
            ## 11. Salvar resultados

            A célula final atualiza a base limpa, auditorias, previsões de teste, métricas e gráficos usados na apresentação e no relatório.
            """
        ),
        code(
            """
            # Atualiza arquivos, métricas e gráficos da entrega.
            generate_charts(dados, divisao, resultados, qualidade)
            resumo = save_outputs(
                dados,
                divisao,
                fim_treino,
                fim_validacao,
                registro_limpeza,
                suspeitas,
                qualidade,
                resultados,
            )
            display(pd.Series(resumo, name="Resultado"))
            print("Entregáveis analíticos atualizados.")
            """
        ),
        markdown(
            """
            ## 12. Respostas finais às perguntas do projeto

            A análise usou as 2.043 trocas da base limpa fornecida pelo professor. O tempo médio foi de **35,66 minutos**, a mediana foi de **35,00 minutos** e **24,8%** das trocas ultrapassaram 42 minutos.
            """
        ),
        markdown(
            """
            ### Pergunta 1. Quantos minutos a troca deve levar?

            Não existe um único tempo correto para todas as trocas. A resposta é a previsão individual produzida pela árvore de regressão a partir das oito informações conhecidas antes de a linha parar.

            Nos **403 registros de teste**, a árvore de profundidade 5 apresentou:

            - **MAE de 2,12 minutos**, ou seja, diferença absoluta média de 2,12 minutos entre o tempo previsto e o observado;
            - **R² de 0,886**, indicando que o modelo explica 88,6% da variação observada nesse período;
            - redução de **66,2% no erro** em comparação com a referência pela mediana, cujo MAE foi de 6,27 minutos.

            Portanto, para uma nova troca, a coluna `tempo_previsto_min` é a resposta estimada. O MAE resume o erro médio observado no teste e não deve ser interpretado como margem garantida para cada caso.
            """
        ),
        markdown(
            """
            ### Pergunta 2. A troca deve ultrapassar 42 minutos?

            A árvore de classificação responde **Sim** quando identifica risco acima do limite operacional e **Não** nos demais casos. Entre as **102 trocas realmente demoradas** no teste:

            - **101** foram identificadas corretamente;
            - **1** não foi detectada;
            - **24** trocas abaixo do limite geraram falso alarme;
            - o `recall` foi de **99,0%**, a precisão de **80,8%** e o F1 de **89,0%**.

            Assim, o modelo encontra a maior parte das trocas demoradas e pode orientar a priorização do apoio. Ele não substitui a decisão do supervisor, pois ainda existem casos perdidos e falsos alarmes.
            """
        ),
        markdown(
            """
            ### Aplicação operacional

            Os resultados respondem positivamente à pergunta central do projeto: os dados disponíveis antes da troca contêm informação suficiente para estimar a duração e antecipar o risco. A aplicação recomendada é ordenar as próximas trocas pela probabilidade de atraso, consultar o tempo estimado e direcionar primeiro o apoio humano para os maiores riscos.

            Como a base é sintética, a decisão de uso real depende de uma validação com dados observados na fábrica e de acompanhamento contínuo dos erros.
            """
        ),
        code(
            """
            respostas_finais = pd.DataFrame(
                [
                    {
                        "Pergunta": "Quantos minutos a troca deve levar?",
                        "Resposta baseada no teste": (
                            f"Mediana observada de {resumo['target_median']:.1f} min; "
                            f"previsão individual com MAE de {resumo['test_mae']:.2f} min "
                            f"e R² de {resumo['test_r2']:.3f}."
                        ),
                    },
                    {
                        "Pergunta": "A troca deve ultrapassar 42 minutos?",
                        "Resposta baseada no teste": (
                            f"Na base, {100 * resumo['delayed_rate']:.1f}% ultrapassaram o limite. "
                            f"O modelo encontrou {resumo['true_positive']} das "
                            f"{resumo['true_positive'] + resumo['false_negative']} trocas demoradas, "
                            f"com recall de {100 * resumo['test_recall']:.1f}%."
                        ),
                    },
                ]
            )
            display(
                respostas_finais.style.hide(axis="index").set_properties(
                    **{"white-space": "normal", "text-align": "left"}
                )
            )
            """
        ),
        markdown(
            """
            ## 13. Perguntas gerais do curso

            Esta seção responde às perguntas gerais que todas as equipes respondem, usando apenas números já calculados nas seções anteriores.
            """
        ),
        markdown(
            """
            ### Que problemas de registro vocês encontraram? Como trataram cada um e conferiram o resultado?

            O arquivo original (`N4_TrocaSMT.csv`, primeira versão da base) trouxe oito tipos de problema de registro: **14** duplicatas exatas; espaços nas bordas de texto (**191** casos); grafias diferentes para a mesma categoria (**161** casos); vírgulas decimais no lugar do ponto (**189** casos); o código-sentinela `9999` (**48** casos); datas no formato `dd/mm/aaaa` misturadas ao formato internacional (**81** casos); e medidas fora dos critérios didáticos, como alimentadores negativos ou kit acima de 100% (**58** casos).

            **Tratamento:** só as duplicatas exatas foram removidas. Nos demais casos, apenas o valor afetado virou ausente no campo correspondente, porque as outras colunas daquele registro continuam confiáveis. Os alvos não foram alterados por essas regras.

            **Conferência:** cada correção foi registrada em uma tabela de auditoria, e a nossa limpeza reproduziu exatamente as entradas da base limpa do professor (`N4_limpo.csv`), que é a base usada nas análises deste notebook. Nessa versão final, só os valores dos alvos (`tempo_troca_min` e `troca_demorada`) diferem da primeira versão; as contagens acima descrevem o arquivo original.
                        """
        ),
        markdown(
            """
            ### Quais informações ficaram ausentes? Como isso afeta a análise?

            Depois da limpeza, cinco entradas numéricas ficaram com ausências: `experiencia_operador_meses` (124 casos, 6,07%), `componentes_novos` (88 casos, 4,31%), `kit_preparado_pct` (54 casos, 2,64%), `tamanho_lote_placas` (32 casos, 1,57%) e `alimentadores_a_trocar` (22 casos, 1,08%). As três entradas de texto (`linha_smt`, `muda_familia`, `turno`) não ficaram com ausências, e nenhum registro do alvo `tempo_troca_min` ficou ausente, então nenhuma troca foi perdida por falta de resposta.

            **Efeito na análise:** ausência não foi tratada como zero, porque zero teria um significado diferente (por exemplo, zero meses de experiência). O pipeline preenche essas lacunas pela mediana aprendida somente no treino (seção 6), aplicada igual à validação e ao teste, para não vazar informação. Como a maior ausência fica em 6,07%, o impacto esperado é pequeno, mas a entrada mais afetada — experiência do operador — é também uma das quatro com maior relação com o resultado (próxima pergunta), o que pede atenção redobrada nela.
            """
        ),
        code(
            """
            # Ausências por entrada, já calculadas no pipeline (seção 3).
            display(qualidade)
            """
        ),
        markdown(
            """
            ### Como o resultado varia entre os casos e os grupos?

            O tempo de troca varia bastante entre casos individuais: de cerca de 17 a 59 minutos, com média de **35,66 minutos** e mediana de **35,00 minutos** — a diferença entre as duas mostra uma cauda de casos mais longos, visível no histograma (gráfico 01).

            Entre grupos, a variação não é uniforme:

            - **Mudar de família de produto** é o fator com maior diferença: média de **40,71 minutos** quando muda contra **31,78 minutos** quando não muda, e **45,5%** das trocas com mudança de família ultrapassam 42 minutos, contra **8,9%** sem mudança — mais de cinco vezes o risco.
            - **Entre as linhas SMT**, a SMT3 teve o maior tempo médio (**38,34 min**) e a maior taxa de trocas demoradas (**35,5%**), enquanto SMT1 e SMT2 ficaram próximas uma da outra (34,34 e 34,10 min; 19,9% e 18,2%).
            - **Entre turnos**, a variação foi pequena: médias entre 35,14 e 36,20 minutos e taxas de trocas demoradas entre 22,8% e 27,3%, sem um turno que se destaque como nas outras duas comparações.

            O gráfico 03 (risco por kit preparado e família) mostra esse cruzamento: o risco de troca demorada sobe quando o kit está pouco preparado e sobe ainda mais quando, ao mesmo tempo, há mudança de família.
            """
        ),
        code(
            """
            # Variação do tempo médio e da taxa de trocas demoradas por grupo.
            for coluna in ["linha_smt", "turno", "muda_familia"]:
                tabela_grupo = dados.groupby(coluna, observed=True).agg(
                    casos=("tempo_troca_min", "size"),
                    tempo_medio_min=("tempo_troca_min", "mean"),
                    pct_demorada=("troca_demorada", "mean"),
                )
                tabela_grupo["pct_demorada"] = (100 * tabela_grupo["pct_demorada"]).round(1)
                print(f"Variação por {coluna}:")
                display(tabela_grupo.round(2))
            """
        ),
        markdown(
            """
            ### Quais características apresentam relações com o resultado e parecem úteis para fazer previsões? Que gráficos ou tabelas sustentam essa interpretação?

            A importância de característica da árvore de regressão (gráfico 07) mostra que três entradas concentram quase toda a capacidade preditiva: **quantidade de alimentadores a trocar** (47,1% da importância), **mudança de família de produto** (29,1%) e **percentual do kit já preparado** (22,2%). Juntas, essas três entradas respondem por mais de 98% da importância total. Experiência do operador, componentes novos, tamanho do lote, turno e linha SMT contribuíram muito pouco.

            Essa ordem é coerente com a leitura exploratória da seção 5 (gráficos 02 e 03): mais alimentadores a trocar e kit menos preparado aparecem associados a tempos maiores, e mudar de família eleva o risco principalmente quando o kit está pouco preparado. A pergunta anterior mostra a mesma hierarquia nos números agregados por grupo. São associações observadas nos dados de treino, não relações causais comprovadas.
            """
        ),
        code(
            """
            # Importância de característica da árvore de regressão escolhida (gráfico 07).
            display(resultados["regression_importance"].round(3))
            """
        ),
        markdown(
            """
            ### O modelo erra menos que uma referência simples? Qual foi a diferença?

            Sim, nas duas tarefas o modelo escolhido errou menos que a referência simples, sempre medido no teste reservado:

            - Na **regressão**, a árvore de profundidade 5 teve MAE de **2,12 minutos**, contra **6,27 minutos** da referência pela mediana do treino — redução de **66,2%** no erro, com R² de 0,886.
            - Na **classificação**, a referência (sempre prever a classe mais comum) não encontra nenhuma troca demorada, ou seja, recall de **0%**. A árvore de profundidade 3 alcançou recall de **99,0%**, precisão de **80,8%** e F1 de **89,0%** — uma diferença grande, porque a referência simplesmente não serve para a decisão operacional de priorizar apoio.
            """
        ),
        markdown(
            """
            ### Quantos casos com problema o modelo encontra, quantos deixa passar e quantos falsos alarmes produz?

            No teste, entre as **102** trocas realmente demoradas, o classificador encontrou **101** (verdadeiros positivos) e deixou passar **1** (falso negativo). Entre as **301** trocas realmente dentro do limite, ele gerou **24** falsos alarmes (falsos positivos) e classificou corretamente **277** como não demoradas (verdadeiros negativos). Isso dá recall de **99,0%** (101 de 102) e precisão de **80,8%** (101 dos 125 alertas emitidos), conforme o gráfico 06 (matriz de confusão).
            """
        ),
        markdown(
            """
            ### Que decisão os resultados poderiam apoiar? O que os dados não permitem concluir?

            **Decisão apoiada:** antes de cada troca, ordenar os casos pela probabilidade de ultrapassar 42 minutos e direcionar primeiro o apoio disponível (pessoas, preparação extra de kit) para os casos de maior risco, usando o tempo previsto pela árvore de regressão como apoio ao planejamento da linha (seção 9).

            **O que os dados não permitem concluir:**

            - **Causa e efeito:** associações como "kit menos preparado aumenta o tempo" são leituras observacionais, não testadas com um experimento controlado.
            - **Desempenho em produção real:** a base é sintética, preparada para o curso, então o MAE de 2,12 minutos e o recall de 99,0% não garantem o mesmo resultado numa fábrica real.
            - **Validade ao longo do tempo:** mudanças no processo, na equipe ou nos produtos podem reduzir o desempenho do modelo, algo que este estudo não acompanha.
            - **Garantia por caso individual:** o MAE e o recall são médias do teste; algumas trocas específicas erram mais do que esses números sugerem, e o modelo ainda pode deixar passar trocas demoradas (1 de 102 no teste) e gera falsos alarmes (24 no teste).
            """
        ),
    ]
    nbf.write(notebook, OUTPUT)
    print(f"Notebook criado em: {OUTPUT}")


if __name__ == "__main__":
    build_notebook()
