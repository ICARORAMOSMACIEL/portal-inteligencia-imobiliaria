"""Interface do comparador; referências de visitantes ficam isoladas por sessão."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from comparador_precos import (
    COLUNAS, MIN_COMPARAVEIS, RESTRICOES, STATUS, TOPOGRAFIAS, Consulta,
    base_demonstracao, base_vazia, comparar, deduplicar, exportar_csv, ler_csv,
    reais, relatorio_html, validar_base,
)


BASE_PATH = Path(__file__).resolve().parent / "data" / "terrenos_mercado.csv"


def _hoje():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def _limpar_resultado():
    st.session_state.pop("precos_resultado", None)


def _trocar_modo():
    _limpar_resultado()
    if st.session_state.precos_demo:
        st.session_state.update(cmp_bairro="Costa e Silva", cmp_area=500.0,
                                cmp_preco=500000.0, cmp_zona="SA-02", cmp_topografia="Plano",
                                cmp_restricoes="Sem restrições identificadas", cmp_ref="FICTICIO-ALVO", cmp_url="")
    else:
        for key in ("cmp_bairro", "cmp_area", "cmp_preco", "cmp_zona", "cmp_topografia", "cmp_restricoes", "cmp_ref", "cmp_url"):
            st.session_state.pop(key, None)


def _mostrar_base(df):
    nomes = {
        "referencia_lote": "Referência do lote", "bairro": "Bairro", "area_m2": "Área (m²)",
        "preco_anunciado": "Preço pedido (R$)", "preco_m2": "Preço/m² (R$)", "sigla_z": "Zona",
        "topografia": "Topografia", "restricoes": "Restrições", "fonte": "Fonte",
        "url": st.column_config.LinkColumn("Anúncio", display_text="Abrir fonte"),
        "data_verificacao": "Verificado em", "status": "Situação",
    }
    colunas = [c for c in nomes if c in df.columns]
    st.dataframe(df[colunas], hide_index=True, width="stretch", column_config=nomes)


def _carregar_base():
    if "precos_base" in st.session_state:
        return
    try:
        raw = ler_csv(BASE_PATH.read_bytes()) if BASE_PATH.exists() else base_vazia()
        dados, erros = validar_base(raw, _hoje())
        st.session_state.precos_base = dados[~dados.demonstracao.astype(bool)].copy()
        st.session_state.precos_problemas = erros
    except (ValueError, OSError) as exc:
        st.session_state.precos_base = base_vazia()
        st.session_state.precos_problemas = pd.DataFrame([{"Linha do CSV": "Arquivo", "Motivo": str(exc)}])


def _formulario_terreno(base):
    for key, value in {
        "cmp_bairro": "", "cmp_area": float(st.session_state.get("area_terreno", 500.0)),
        "cmp_preco": 0.0, "cmp_zona": st.session_state.get("zona_consultada", ""),
        "cmp_topografia": "Não verificada", "cmp_restricoes": "Não verificadas",
        "cmp_ref": "", "cmp_url": "",
    }.items():
        st.session_state.setdefault(key, value)
    with st.form("comparar_preco"):
        st.subheader("Qual terreno você quer analisar?")
        a, b = st.columns(2)
        bairro = a.text_input("Bairro em Joinville", key="cmp_bairro", placeholder="Ex.: Costa e Silva")
        zona = b.text_input("Zoneamento do lote", key="cmp_zona", placeholder="Ex.: SA-02", help="Use a zona confirmada na consulta construtiva ou em documento do lote.")
        area = a.number_input("Área do terreno (m²)", min_value=1.0, step=10.0, key="cmp_area")
        preco = b.number_input("Preço pedido pelo terreno (R$)", min_value=0.0, step=10000.0, key="cmp_preco")
        topografia = a.selectbox("Topografia", TOPOGRAFIAS, key="cmp_topografia")
        restricoes = b.selectbox("Condições verificadas", RESTRICOES, key="cmp_restricoes",
                                  help="Esta versão compara lotes sem restrições identificadas. Condições desconhecidas ou restrições precisam ser verificadas antes.")
        referencia = a.text_input("Referência do lote (se estiver na base)", key="cmp_ref",
                                   help="Use a mesma referência da base para impedir que o terreno seja comparado consigo mesmo.")
        url = b.text_input("Link do anúncio analisado (se houver)", key="cmp_url", placeholder="https://...")
        with st.expander("Critérios da comparação"):
            margem = st.slider("Variação máxima da área (%)", min_value=10, max_value=50, value=30, step=5, key="cmp_margem")
            dias = st.selectbox("Referências verificadas nos últimos", [30, 90, 180, 365], index=2,
                                format_func=lambda n: f"{n} dias", key="cmp_dias")
            st.caption(f"Mesmo bairro, zoneamento e topografia; mínimo de {MIN_COMPARAVEIS} terrenos únicos. A faixa mostra a metade central dos preços por m² encontrados.")
        submitted = st.form_submit_button("Comparar preço", type="primary", width="stretch")
    if submitted:
        _limpar_resultado()
        try:
            consulta = Consulta(bairro, area, preco, zona, topografia, restricoes,
                                referencia, url, margem / 100, dias, bool(st.session_state.precos_demo))
            st.session_state.precos_resultado = comparar(base, consulta, _hoje())
        except ValueError as exc:
            st.error(str(exc))


def _resultado():
    resultado = st.session_state.get("precos_resultado")
    if resultado is None:
        return
    c = resultado["consulta"]
    st.divider()
    st.subheader(resultado["status"])
    st.caption(f"Comparação enviada: {c.bairro} · {c.sigla_z} · {c.area_m2:g} m² · preço pedido de {reais(c.preco_anunciado)}")
    if c.demonstracao:
        st.warning("DEMONSTRAÇÃO: todos os anúncios e preços deste resultado são fictícios.")
    if resultado["motivo"]:
        st.info(resultado["motivo"])
    if resultado["mediana_m2"] is not None:
        p1, p2, p3 = st.columns(3)
        p1.metric("Preço pedido por m²", reais(resultado["preco_m2_alvo"]))
        p2.metric("Mediana dos comparáveis por m²", reais(resultado["mediana_m2"]))
        p3.metric("Diferença para a mediana", f"{resultado['diferenca_pct']:+.1f}%".replace(".", ","), help="Comparação com a mediana dos anúncios selecionados.")
        st.info(f"Faixa central dos comparáveis para {c.area_m2:g} m²: **{reais(resultado['faixa_inferior'])} a {reais(resultado['faixa_superior'])}**")
        st.caption("Faixa dos percentis 25 a 75 do preço/m², multiplicada pela sua área. Não é intervalo de confiança nem previsão do preço de venda.")
    st.markdown(f"**{resultado['n']} terrenos usados na comparação**")
    if not resultado["comparaveis"].empty:
        _mostrar_base(resultado["comparaveis"])
    with st.expander("Por que estes terrenos foram selecionados?"):
        st.dataframe(resultado["etapas"], hide_index=True, width="stretch")
        st.write("A referência do lote e o link identificam anúncios repetidos. A atualização mais recente prevalece, inclusive quando informa venda ou indisponibilidade. Use a mesma referência para o mesmo lote anunciado por fontes diferentes.")
        st.write("A comparação ainda não ajusta frente, posição na rua, documentação ou condições que não estejam cadastradas. Ela usa preços pedidos, que podem diferir dos valores negociados.")
    if not resultado["invalidos"].empty:
        st.warning("Algumas linhas inválidas não entraram na comparação.")
        st.dataframe(resultado["invalidos"], hide_index=True)
    st.download_button("Baixar relatório da comparação", relatorio_html(resultado),
                       file_name="DEMONSTRACAO_comparacao.html" if c.demonstracao else "comparacao_terreno.html",
                       mime="text/html", key="baixar_comparacao", width="stretch")


def _gerenciar_base():
    st.subheader("Suas referências de mercado")
    st.write("Cadastre terrenos que você verificou ou importe um CSV. Use a mesma referência para anúncios do mesmo lote, mesmo quando forem de imobiliárias diferentes.")
    st.info("As alterações desta tela ficam nesta sessão. Baixe a base atualizada para guardar seus cadastros e importar novamente depois.")
    if not st.session_state.precos_problemas.empty:
        st.warning("A base inicial contém linhas que precisam de revisão.")
        st.dataframe(st.session_state.precos_problemas, hide_index=True)
    a, b = st.columns(2)
    a.download_button("Baixar modelo CSV vazio", exportar_csv(base_vazia()), "modelo_terrenos.csv", "text/csv", width="stretch")
    b.download_button("Baixar minha base atualizada", exportar_csv(st.session_state.precos_base), "terrenos_mercado.csv", "text/csv", width="stretch")
    with st.expander("Importar uma base CSV"):
        arquivo = st.file_uploader("CSV com as colunas do modelo", type=["csv"], key="precos_upload")
        st.caption("A importação substitui as referências desta sessão. Aceita UTF-8, separador vírgula ou ponto e vírgula e datas AAAA-MM-DD ou DD/MM/AAAA.")
        if st.button("Importar CSV", disabled=arquivo is None):
            try:
                df, erros = validar_base(ler_csv(arquivo.getvalue()), _hoje())
                if not erros.empty:
                    st.error("A importação não foi aplicada. Corrija as linhas abaixo e envie o arquivo novamente.")
                    st.dataframe(erros, hide_index=True)
                elif not df.empty and df.demonstracao.any():
                    st.error("A base real não aceita dados marcados como demonstração. Use o modo de demonstração separado.")
                else:
                    st.session_state.precos_base = df
                    st.session_state.precos_problemas = pd.DataFrame()
                    _limpar_resultado()
                    st.session_state.precos_aviso = f"Base importada: {len(df)} registros. Baixe uma cópia para guardar."
                    st.rerun()
            except (ValueError, OSError) as exc:
                st.error(str(exc))
    with st.expander("Cadastrar ou atualizar uma referência"):
        with st.form("cadastrar_referencia", clear_on_submit=False):
            a, b = st.columns(2)
            ref = a.text_input("Referência única do lote", key="cad_ref", help="Pode ser seu código interno ou o endereço completo do lote. Repita esse código ao atualizar o mesmo terreno.")
            bairro = b.text_input("Bairro", key="cad_bairro")
            area = a.number_input("Área (m²)", min_value=1.0, value=500.0, step=10.0, key="cad_area")
            preco = b.number_input("Preço anunciado (R$)", min_value=0.0, value=0.0, step=10000.0, key="cad_preco")
            zona = a.text_input("Zona urbanística", key="cad_zona")
            topo = b.selectbox("Topografia do lote", TOPOGRAFIAS, index=4, key="cad_topo")
            restricoes = a.selectbox("Restrições verificadas", RESTRICOES, index=2, key="cad_restricoes")
            status = b.selectbox("Situação do anúncio", STATUS, key="cad_status")
            fonte = a.text_input("Fonte / imobiliária", key="cad_fonte")
            url = b.text_input("Link da fonte", key="cad_url")
            dia = a.date_input("Data da verificação", value=_hoje(), max_value=_hoje(), key="cad_data")
            enviado = st.form_submit_button("Adicionar à minha base", type="primary")
        if enviado:
            registro = pd.DataFrame([dict(zip(COLUNAS, [ref, "Terreno", "Joinville", bairro, area,
                preco, zona, topo, restricoes, fonte, url, dia.isoformat(), status, False]))])
            df, erros = validar_base(registro, _hoje())
            if not erros.empty:
                for erro in erros["Motivo"]:
                    st.error(erro)
            else:
                anterior = st.session_state.precos_base
                st.session_state.precos_base = df.copy() if anterior.empty else pd.concat([anterior, df], ignore_index=True)
                _limpar_resultado()
                st.session_state.precos_aviso = "Referência adicionada nesta sessão. Baixe a base atualizada para guardar."
                st.rerun()
    base = st.session_state.precos_base
    if base.empty:
        st.info("Sua base ainda está vazia. Cadastre referências verificadas para começar.")
    else:
        st.caption(f"{len(base)} registros · {len(deduplicar(base))} terrenos únicos. Atualizações anteriores permanecem no CSV para histórico.")
        _mostrar_base(base)


def renderizar_comparador():
    _carregar_base()
    st.header("Comparador de preços de terrenos")
    st.write("Veja como o preço pedido se posiciona entre anúncios de terrenos semelhantes em Joinville.")
    st.checkbox("Experimentar com dados fictícios", key="precos_demo", on_change=_trocar_modo)
    demo = st.session_state.precos_demo
    if demo:
        st.warning("Modo de demonstração: a comparação usa anúncios e preços fictícios. Sua base real continua na aba Gerenciar referências.")
    if "precos_aviso" in st.session_state:
        st.success(st.session_state.pop("precos_aviso"))
    base = base_demonstracao(_hoje()) if demo else st.session_state.precos_base
    comparar_tab, base_tab = st.tabs(["Comparar terreno", "Gerenciar referências"])
    with comparar_tab:
        if base.empty:
            st.info("Ainda não há referências de mercado. Cadastre ou importe seus terrenos em Gerenciar referências, ou experimente a demonstração.")
        _formulario_terreno(base)
        _resultado()
    with base_tab:
        _gerenciar_base()
