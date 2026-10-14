import glob
import os
import re
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def escolher_arquivo_csv(pasta_trabalho):
    arquivos = sorted(glob.glob(os.path.join(pasta_trabalho, '*.csv')))

    if not arquivos:
        print("Nenhum arquivo .csv encontrado na pasta do script.")
        sys.exit(1)

    if len(arquivos) == 1:
        return arquivos[0]

    print("\nArquivos CSV encontrados:")
    for i, arq in enumerate(arquivos, start=1):
        print(f"  {i} - {os.path.basename(arq)}")
    while True:
        escolha = input("Escolha o arquivo (número): ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(arquivos):
            return arquivos[int(escolha) - 1]
        print("Opção inválida.")


def ler_csv(caminho):
    try:
        df = pd.read_csv(caminho, sep=None, engine='python')
    except UnicodeDecodeError:
        df = pd.read_csv(caminho, sep=None, engine='python', encoding='latin-1')

    if df.shape[1] == 1:
        df = pd.read_csv(caminho, sep=';')

    df.columns = [str(c).strip() for c in df.columns]
    return df


def tentar_numerico(serie, limite=0.8):
    if pd.api.types.is_numeric_dtype(serie):
        return serie
    convertida = pd.to_numeric(
        serie.astype(str).str.strip().str.replace(',', '.', regex=False),
        errors='coerce'
    )
    if convertida.notna().mean() >= limite:
        return convertida
    return None


def tentar_datetime(serie, limite=0.8):
    try:
        convertida = pd.to_datetime(serie, errors='coerce')
    except Exception:
        return None
    if convertida.notna().mean() >= limite:
        return convertida
    return None


def preparar_eixo(serie, eixo):
    num = tentar_numerico(serie)
    if num is not None:
        return num, 'numerico'

    if eixo == 'x':
        data = tentar_datetime(serie)
        if data is not None:
            return data, 'data'
        return serie.astype(str), 'categorico'

    return None, None


def listar_colunas(df):
    print("\nColunas disponíveis:\n")
    for i, col in enumerate(df.columns, start=1):
        print(f"  {i} - {col}")
    print()


def pedir_coluna(df, mensagem):
    colunas = list(df.columns)
    while True:
        entrada = input(mensagem).strip()
        if entrada.isdigit() and 1 <= int(entrada) <= len(colunas):
            return colunas[int(entrada) - 1]
        if entrada in colunas:
            return entrada
        print(f"Opção inválida. Digite um número de 1 a {len(colunas)}.")


def pedir_tipo_grafico():
    print("\nTipo de gráfico:")
    print("  1 - Linha")
    print("  2 - Dispersão (pontos)")
    print("  3 - Barras")
    while True:
        escolha = input("Escolha (Enter = 1): ").strip() or '1'
        if escolha in ('1', '2', '3'):
            return {'1': 'linha', '2': 'dispersao', '3': 'barras'}[escolha]
        print("Opção inválida.")


def nome_seguro(texto):
    return re.sub(r'[^\w\-]+', '_', texto).strip('_')


def gerar_grafico(df, col_x, col_y, tipo, pasta_saida, nome_base):
    x, tipo_x = preparar_eixo(df[col_x], 'x')
    y, _ = preparar_eixo(df[col_y], 'y')

    if y is None:
        print(f"\n A coluna '{col_y}' não é numérica e não pode ser usada no eixo Y.")
        return

    dados = pd.DataFrame({'x': x, 'y': y}).dropna()
    if dados.empty:
        print("\n Não há dados válidos para essas colunas.")
        return

    if tipo_x in ('numerico', 'data') and tipo != 'dispersao':
        dados = dados.sort_values('x')

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6))
    cor = '#1f77b4'

    if tipo == 'linha':
        marcador = 'o' if len(dados) <= 60 else None
        ax.plot(dados['x'], dados['y'], '-', marker=marcador, color=cor, linewidth=2)
    elif tipo == 'dispersao':
        ax.scatter(dados['x'], dados['y'], color=cor, alpha=0.7, edgecolor='white')
    else:
        if len(dados) > 100:
            print("⚠ Muitos pontos para barras; o gráfico pode ficar poluído.")
        ax.bar(dados['x'].astype(str) if tipo_x == 'categorico' else dados['x'],
               dados['y'], color=cor)

    ax.set_title(f'{col_y} em função de {col_x}', fontsize=14, fontweight='bold')
    ax.set_xlabel(col_x)
    ax.set_ylabel(col_y)

    if tipo_x == 'categorico' and dados['x'].nunique() > 10:
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    if tipo_x == 'data':
        fig.autofmt_xdate()

    plt.tight_layout()

    nome_arquivo = f"grafico_{nome_seguro(nome_base)}_{nome_seguro(col_y)}_vs_{nome_seguro(col_x)}.png"
    caminho_imagem = os.path.join(pasta_saida, nome_arquivo)
    plt.savefig(caminho_imagem, dpi=300, bbox_inches='tight')
    print(f"\nSucesso! Gráfico salvo em:\n{caminho_imagem}")
    plt.show()


def main():
    pasta_trabalho = os.path.dirname(os.path.abspath(__file__))
    caminho_csv = escolher_arquivo_csv(pasta_trabalho)
    print(f"\nLendo dados de: {os.path.basename(caminho_csv)}")

    df = ler_csv(caminho_csv)
    print(f"{len(df)} linhas e {df.shape[1]} colunas carregadas.")

    nome_base = os.path.splitext(os.path.basename(caminho_csv))[0]

    while True:
        listar_colunas(df)
        col_x = pedir_coluna(df, "Escolha a coluna do eixo X (número): ")
        col_y = pedir_coluna(df, "Escolha a coluna do eixo Y (número): ")
        tipo = pedir_tipo_grafico()

        gerar_grafico(df, col_x, col_y, tipo, pasta_trabalho, nome_base)

        outro = input("\nGerar outro gráfico? (s/N): ").strip().lower()
        if outro not in ('s', 'sim', 'y'):
            break


if __name__ == "__main__":
    main()
