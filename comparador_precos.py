"""Comparação exploratória de preços anunciados de terrenos em Joinville.

Não estima preços de transação. Os limites de amostra são regras do produto,
não requisitos de uma norma de avaliação. Nenhuma função acessa sites externos.
"""

from dataclasses import dataclass
from datetime import date, datetime
from html import escape
import io
import math
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd


COLUNAS = [
    "referencia_lote", "tipo", "cidade", "bairro", "area_m2",
    "preco_anunciado", "sigla_z", "topografia", "restricoes", "fonte",
    "url", "data_verificacao", "status", "demonstracao",
]
TOPOGRAFIAS = ["Plano", "Aclive", "Declive", "Irregular", "Não verificada"]
RESTRICOES = ["Sem restrições identificadas", "Com restrições", "Não verificadas"]
STATUS = ["Disponível", "Em negociação", "Vendido", "Indisponível"]
MIN_COMPARAVEIS = 5
MAX_DISPERSAO = 0.60


def normalizar(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.casefold().strip().split())


def numero(valor):
    if isinstance(valor, bool):
        raise ValueError("valor numérico inválido")
    if isinstance(valor, str):
        valor = valor.strip().replace("R$", "").replace("\u00a0", "").replace(" ", "")
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")
    try:
        resultado = float(valor)
    except (ValueError, TypeError):
        raise ValueError("valor numérico inválido") from None
    if not math.isfinite(resultado) or resultado <= 0:
        raise ValueError("informe um número positivo e finito")
    return resultado


def data_validada(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(valor).strip(), formato).date()
        except ValueError:
            pass
    raise ValueError("data deve usar AAAA-MM-DD ou DD/MM/AAAA")


def url_canonica(valor):
    valor = str(valor or "").strip()
    try:
        url = urlsplit(valor)
        if (url.scheme.lower() not in ("http", "https") or not url.hostname
                or url.username or url.password or re.search(r"\s", valor)):
            raise ValueError
        _ = url.port
    except ValueError:
        raise ValueError("URL deve ser um link http(s) válido e sem credenciais") from None
    # Preserva parâmetros que identificam o anúncio; remove somente rastreamento.
    query = [(k, v) for k, v in parse_qsl(url.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"),
                       urlencode(sorted(query)), ""))


def base_vazia():
    return pd.DataFrame(columns=COLUNAS)


def ler_csv(conteudo):
    if len(conteudo) > 5 * 1024 * 1024:
        raise ValueError("O arquivo deve ter no máximo 5 MB.")
    texto = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            texto = conteudo.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError("Salve o arquivo como CSV UTF-8.")
    try:
        separador = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
        df = pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, IndexError):
        raise ValueError("Não foi possível ler o CSV. Use o modelo disponível na página.") from None
    if len(df) > 20000:
        raise ValueError("Use até 20 mil registros por arquivo.")
    return df


def validar_base(df, hoje=None):
    """Retorna registros válidos e problemas por linha, sem corrigir dados por suposição."""
    hoje = hoje or date.today()
    faltam = set(COLUNAS[:-1]) - set(df.columns)
    if faltam:
        raise ValueError("Colunas ausentes: " + ", ".join(sorted(faltam)))
    validos, erros = [], []
    for linha, entrada in enumerate(df.to_dict("records"), start=2):
        try:
            registro = {c: str(entrada.get(c, "")).strip() for c in COLUNAS}
            for campo in ("referencia_lote", "bairro", "sigla_z", "fonte"):
                if not registro[campo] or registro[campo].lower() in ("nan", "none"):
                    raise ValueError(f"{campo}: preenchimento obrigatório")
            if normalizar(registro["cidade"]) != "joinville" or normalizar(registro["tipo"]) != "terreno":
                raise ValueError("esta versão aceita somente terrenos de Joinville")
            registro["cidade"], registro["tipo"] = "Joinville", "Terreno"
            for campo in ("area_m2", "preco_anunciado"):
                try:
                    registro[campo] = numero(entrada[campo])
                except ValueError as exc:
                    raise ValueError(f"{campo}: {exc}") from None
            for campo, opcoes in (("topografia", TOPOGRAFIAS), ("restricoes", RESTRICOES), ("status", STATUS)):
                mapa = {normalizar(opcao): opcao for opcao in opcoes}
                if normalizar(registro[campo]) not in mapa:
                    raise ValueError(f"{campo}: use " + ", ".join(opcoes))
                registro[campo] = mapa[normalizar(registro[campo])]
            verificada = data_validada(entrada["data_verificacao"])
            if verificada > hoje:
                raise ValueError("data de verificação no futuro")
            registro["data_verificacao"] = verificada.isoformat()
            registro["url"] = url_canonica(registro["url"])
            demo = normalizar(entrada.get("demonstracao", "false"))
            if demo not in ("", "false", "0", "nao", "true", "1", "sim"):
                raise ValueError("demonstracao: use true ou false")
            registro["demonstracao"] = demo in ("true", "1", "sim")
            validos.append(registro)
        except (ValueError, TypeError) as exc:
            erros.append({"Linha do CSV": linha, "Motivo": str(exc)})
    return pd.DataFrame(validos, columns=COLUNAS), pd.DataFrame(erros, columns=["Linha do CSV", "Motivo"])


def deduplicar(df):
    """Une identidades por referência do lote OU URL; a atualização mais recente vence."""
    if df.empty:
        return df.copy()
    df = df.reset_index(drop=True)
    pais = list(range(len(df)))
    def raiz(i):
        while pais[i] != i:
            pais[i] = pais[pais[i]]
            i = pais[i]
        return i
    vistos = {}
    for i, row in df.iterrows():
        for chave in (("lote", normalizar(row.referencia_lote)), ("url", url_canonica(row.url))):
            if chave in vistos:
                pais[raiz(i)] = raiz(vistos[chave])
            else:
                vistos[chave] = i
    df["_grupo"] = [raiz(i) for i in range(len(df))]
    return (df.sort_values("data_verificacao", kind="stable")
            .drop_duplicates("_grupo", keep="last").drop(columns="_grupo").reset_index(drop=True))


@dataclass(frozen=True)
class Consulta:
    bairro: str
    area_m2: float
    preco_anunciado: float
    sigla_z: str
    topografia: str
    restricoes: str
    referencia_lote: str = ""
    url: str = ""
    tolerancia_area: float = 0.30
    max_dias: int = 180
    demonstracao: bool = False


def comparar(df, consulta, hoje=None):
    hoje = hoje or date.today()
    area, preco = numero(consulta.area_m2), numero(consulta.preco_anunciado)
    if not normalizar(consulta.bairro) or not normalizar(consulta.sigla_z):
        raise ValueError("Informe o bairro e o zoneamento do terreno.")
    if not 0.10 <= consulta.tolerancia_area <= 0.50 or not 1 <= consulta.max_dias <= 365:
        raise ValueError("Critérios de comparação fora do intervalo permitido.")
    if consulta.topografia not in TOPOGRAFIAS or consulta.restricoes not in RESTRICOES:
        raise ValueError("Confira a topografia e as restrições informadas.")
    alvo_url = url_canonica(consulta.url) if consulta.url.strip() else ""
    dados, invalidos = validar_base(df, hoje)
    dados = dados[dados.demonstracao == consulta.demonstracao].copy()
    total = len(dados)
    # Exclui todas as versões do próprio terreno, inclusive URLs vinculadas ao mesmo lote.
    alvo_refs = {normalizar(consulta.referencia_lote)} - {""}
    alvo_urls = {alvo_url} - {""}
    while True:
        ligados = dados[dados.referencia_lote.map(normalizar).isin(alvo_refs) | dados.url.isin(alvo_urls)]
        refs = alvo_refs | set(ligados.referencia_lote.map(normalizar))
        urls = alvo_urls | set(ligados.url)
        if refs == alvo_refs and urls == alvo_urls:
            break
        alvo_refs, alvo_urls = refs, urls
    dados = deduplicar(dados)
    etapas = [{"Critério": "Registros válidos do modo selecionado", "Restantes": total},
              {"Critério": "Terrenos únicos (atualização mais recente)", "Restantes": len(dados)}]
    filtros = [
        ("Exclusão do próprio terreno", ~(dados.referencia_lote.map(normalizar).isin(alvo_refs) | dados.url.isin(alvo_urls))),
        ("Disponíveis", dados.status == "Disponível"),
        (f"Verificados nos últimos {consulta.max_dias} dias", dados.data_verificacao.map(lambda d: (hoje - date.fromisoformat(d)).days <= consulta.max_dias)),
        ("Mesmo bairro", dados.bairro.map(normalizar) == normalizar(consulta.bairro)),
        ("Mesmo zoneamento", dados.sigla_z.map(normalizar) == normalizar(consulta.sigla_z)),
        ("Mesma topografia verificada", (dados.topografia == consulta.topografia) & (dados.topografia != "Não verificada")),
        ("Sem restrições identificadas", dados.restricoes == "Sem restrições identificadas"),
        (f"Área dentro de ±{consulta.tolerancia_area:.0%}", dados.area_m2.between(area * (1 - consulta.tolerancia_area), area * (1 + consulta.tolerancia_area))),
    ]
    mascara = pd.Series(True, index=dados.index, dtype=bool)
    for nome, filtro in filtros:
        mascara &= filtro
        etapas.append({"Critério": nome, "Restantes": int(mascara.sum())})
    comps = dados.loc[mascara].copy()
    comps["preco_m2"] = comps.preco_anunciado / comps.area_m2
    comps = comps.sort_values("preco_m2").reset_index(drop=True)
    resultado = {"consulta": consulta, "data": hoje.isoformat(), "comparaveis": comps,
                 "etapas": pd.DataFrame(etapas), "invalidos": invalidos, "n": len(comps),
                 "status": "Dados insuficientes", "motivo": "", "mediana_m2": None,
                 "faixa_inferior": None, "faixa_superior": None, "referencia_central": None,
                 "diferenca_pct": None, "preco_m2_alvo": preco / area}
    if consulta.topografia == "Não verificada" or consulta.restricoes != "Sem restrições identificadas":
        resultado["motivo"] = "Verifique as condições do lote. Terrenos com restrições exigem análise individual antes da comparação."
        return resultado
    if len(comps) < MIN_COMPARAVEIS:
        resultado["motivo"] = f"Encontrados {len(comps)} terrenos comparáveis. Esta versão exige pelo menos {MIN_COMPARAVEIS} para classificar o preço."
        return resultado
    q1, mediana, q3 = comps.preco_m2.quantile([0.25, 0.50, 0.75]).tolist()
    if (q3 - q1) / mediana > MAX_DISPERSAO:
        resultado["status"] = "Amostra heterogênea"
        resultado["motivo"] = "Os preços dos comparáveis variam demais. Revise localização e características antes de classificar."
        return resultado
    resultado.update(mediana_m2=mediana, faixa_inferior=q1 * area, faixa_superior=q3 * area,
                     referencia_central=mediana * area,
                     diferenca_pct=((preco / area) / mediana - 1) * 100)
    resultado["status"] = ("Abaixo da faixa dos comparáveis" if preco / area < q1 else
                           "Acima da faixa dos comparáveis" if preco / area > q3 else
                           "Dentro da faixa dos comparáveis")
    return resultado


def reais(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exportar_csv(df):
    copia = df.copy()
    for coluna in copia.select_dtypes(include=["object", "string"]).columns:
        copia[coluna] = copia[coluna].map(
            lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v)
    return copia.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")


def base_demonstracao(hoje=None):
    hoje = hoje or date.today()
    registros = []
    for i, (area, valor) in enumerate(zip([450, 480, 490, 500, 510, 520, 540, 550],
                                         [800, 820, 840, 860, 880, 900, 920, 940]), start=1):
        registros.append(dict(zip(COLUNAS, [
            f"FICTICIO-{i:02}", "Terreno", "Joinville", "Costa e Silva", area,
            area * valor, "SA-02", "Plano", "Sem restrições identificadas",
            "Exemplo fictício", f"https://example.com/terreno-ficticio-{i}",
            hoje.isoformat(), "Disponível", True,
        ])))
    return pd.DataFrame(registros, columns=COLUNAS)


def relatorio_html(resultado):
    c = resultado["consulta"]
    titulo = "Comparação de preços anunciados — terrenos de Joinville"
    demo = "<p class='aviso'><b>DEMONSTRAÇÃO — DADOS FICTÍCIOS. Sem valor de referência de mercado.</b></p>" if c.demonstracao else ""
    faixa = "Não calculada"
    if resultado["mediana_m2"] is not None:
        faixa = f"{reais(resultado['faixa_inferior'])} a {reais(resultado['faixa_superior'])}"
    resumo = {
        "Terreno analisado": c.referencia_lote or "Não informado",
        "Bairro / zona": f"{c.bairro} / {c.sigla_z}", "Topografia": c.topografia,
        "Área": f"{c.area_m2:.2f} m²", "Preço pedido": reais(c.preco_anunciado),
        "Preço pedido por m²": reais(resultado["preco_m2_alvo"]),
        "Resultado": resultado["status"], "Faixa central dos comparáveis × área do lote": faixa,
        "Comparáveis": str(resultado["n"]), "Data da análise": resultado["data"],
        "Critérios": f"Mesmo bairro, zona e topografia; área ±{c.tolerancia_area:.0%}; até {c.max_dias} dias; sem restrições identificadas.",
    }
    if resultado["mediana_m2"] is not None:
        resumo["Mediana por m²"] = reais(resultado["mediana_m2"])
        resumo["Diferença para a mediana"] = f"{resultado['diferenca_pct']:+.1f}%".replace(".", ",")
    linhas = "".join(f"<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in resumo.items())
    tabela = resultado["comparaveis"].to_html(index=False, escape=True, border=0)
    texto = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>{titulo}</title>
<style>body{{font:15px Arial,sans-serif;color:#173048;max-width:1120px;margin:40px auto;padding:0 24px}}h1{{font-size:27px}}table{{border-collapse:collapse;width:100%;font-size:12px;overflow-wrap:anywhere}}th,td{{padding:9px;border-bottom:1px solid #dbe5ed;text-align:left}}th{{background:#f0f5f8}}.aviso{{padding:16px;background:#fff2d8}}@media print{{body{{margin:0;padding:0}}table{{font-size:9px}}}}</style>
<h1>{titulo}</h1>{demo}<table>{linhas}</table><p>{escape(resultado['motivo'])}</p>
<h2>Como interpretar</h2><p>A faixa representa os percentis 25 e 75 dos preços por m² dos anúncios comparáveis, multiplicados pela área do terreno analisado. É a metade central da amostra, não um intervalo de confiança nem o preço provável de venda. A mediana é o valor central dos anúncios.</p>
<p>Comparação exploratória de preços pedidos. Não inclui vistoria, análise documental ou ajustes automáticos por frente, posição na rua ou outras características não cadastradas. Preço de anúncio pode diferir do valor negociado.</p>
<h2>Referências utilizadas</h2>{tabela}<h2>Seleção da amostra</h2>{resultado['etapas'].to_html(index=False, escape=True, border=0)}
</html>"""
    return texto.encode("utf-8")
