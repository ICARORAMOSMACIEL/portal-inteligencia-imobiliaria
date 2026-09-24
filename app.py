import io
import os
import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from shapely.geometry import Point
from streamlit_folium import st_folium

# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA & SESSION STATE
# ============================================================

st.set_page_config(
    page_title="Portal de Inteligência Imobiliária - Joinville",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 Portal de Inteligência Imobiliária - Joinville/SC")

st.markdown(
    "Plataforma de viabilidade construtiva (LOUOS/SIMGeo), "
    "simulador de potencial e avaliação financeira de VGV."
)

# Inicialização de variáveis no session_state
if "creditos_disponiveis" not in st.session_state:
    st.session_state["creditos_disponiveis"] = 0

if "curtidas" not in st.session_state:
    st.session_state["curtidas"] = 0

if "consultado" not in st.session_state:
    st.session_state.consultado = False

if "lat" not in st.session_state:
    st.session_state.lat = -26.2745

if "lng" not in st.session_state:
    st.session_state.lng = -48.8512

if "area_terreno" not in st.session_state:
    st.session_state.area_terreno = 500.0

if "valor_m2" not in st.session_state:
    st.session_state.valor_m2 = 7500.0

if "eficiencia" not in st.session_state:
    st.session_state.eficiencia = 75.0


# ============================================================
# 2. CARREGAR DADOS (SUPORTE COMPLETO A ZIP E FALLBACK)
# ============================================================


@st.cache_data
def carregar_dados():
    zip_path = os.path.join("data", "shp_zoneamento.zip")
    csv_path = os.path.join("data", "parametros_louos.csv")

    if os.path.exists(zip_path):
        shapefile_path = f"zip://{zip_path}"
    else:
        shapefile_path = os.path.join("data", "Zoneamento", "anexos_II_III.shp")

    gdf = gpd.read_file(shapefile_path)
    df_louos = pd.read_csv(csv_path)

    return gdf, df_louos


gdf_zoneamento, df_louos = carregar_dados()


# ============================================================
# 3. GERAR RELATÓRIO PDF (REPORTLAB)
# ============================================================


def gerar_pdf(
    info,
    lat,
    lng,
    area,
    area_projecao,
    area_basica,
    area_maxima,
    outorga_m2,
    eficiencia,
    area_priv_basica,
    area_priv_maxima,
    valor_m2,
    vgv_basico,
    vgv_maximo,
):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8,
    )

    # TÍTULO
    story.append(
        Paragraph(
            "Relatório de Viabilidade Construtiva e Estudo de VGV - Joinville/SC",
            title_style,
        )
    )
    story.append(Spacer(1, 10))

    # LOCALIZAÇÃO
    story.append(
        Paragraph(
            "<b>1. Localização e Dimensões do Terreno</b>", heading_style
        )
    )

    dados_loc = [
        ["Latitude:", f"{lat:.6f}", "Longitude:", f"{lng:.6f}"],
        ["Área Total do Lote:", f"{area:.2f} m²", "Município:", "Joinville / SC"],
    ]

    t_loc = Table(dados_loc, colWidths=[120, 130, 120, 130])
    t_loc.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )
    story.append(t_loc)
    story.append(Spacer(1, 12))

    # PARÂMETROS URBANÍSTICOS
    story.append(
        Paragraph("<b>2. Parâmetros Urbanísticos (LOUOS)</b>", heading_style)
    )

    dados_urban = [
        ["Zona Urbana:", f"{info['nome_zona']} ({info['sigla_z']})"],
        ["C.A. Básico:", str(info["ca_basico"])],
        ["C.A. Máximo:", str(info["ca_maximo"])],
        ["Taxa de Ocupação (TO):", f"{int(info['taxa_ocupacao'] * 100)}%"],
        ["Gabarito Máximo:", f"{info['gabarito_max_pav']} pavimentos"],
        ["Recuo Frontal Mínimo:", f"{info['recuo_frontal_m']} metros"],
    ]

    t_urban = Table(dados_urban, colWidths=[200, 300])
    t_urban.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )
    story.append(t_urban)
    story.append(Spacer(1, 12))

    # POTENCIAL E VGV
    story.append(
        Paragraph(
            "<b>3. Potencial Construtivo e Estimativa de VGV</b>", heading_style
        )
    )

    dados_potencial = [
        ["Projeção Máxima no Solo:", f"{area_projecao:.2f} m²"],
        ["Área Construtiva Básica:", f"{area_basica:.2f} m²"],
        ["Área Construtiva Máxima:", f"{area_maxima:.2f} m²"],
        ["Potencial Construtivo Adicional:", f"{outorga_m2:.2f} m²"],
        ["Eficiência Vendável Aplicada:", f"{eficiencia:.1f}%"],
        ["Área Privativa Básica Estimada:", f"{area_priv_basica:.2f} m²"],
        ["Área Privativa Máxima Estimada:", f"{area_priv_maxima:.2f} m²"],
        ["Preço Médio de Venda Estimado:", f"R$ {valor_m2:,.2f} / m²"],
        ["VGV Básico Estimado:", f"R$ {vgv_basico:,.2f}"],
        ["VGV Máximo Estimado:", f"R$ {vgv_maximo:,.2f}"],
    ]

    t_pot = Table(dados_potencial, colWidths=[230, 270])
    t_pot.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#93C5FD")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ])
    )
    story.append(t_pot)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ============================================================
# 4. PAINEL DE MONETIZAÇÃO & BARRA LATERAL
# ============================================================


def renderizar_painel_monetizacao():
    st.sidebar.markdown("---")
    st.sidebar.subheader("💳 Seu Saldo de Créditos")
    st.sidebar.info(
        f"Créditos de Análise: **{st.session_state['creditos_disponiveis']}**\n\n"
        f"Total de Curtidas Dadas: 👍 **{st.session_state['curtidas']}**"
    )

    st.sidebar.markdown("### 👍 Ganhar Créditos")
    st.sidebar.caption("Curta a plataforma para ganhar 1 crédito por curtida!")

    if st.sidebar.button("👍 Curtir e Ganhar +1 Crédito", type="primary"):
        st.session_state["curtidas"] += 1
        st.session_state["creditos_disponiveis"] += 1
        st.sidebar.success("Obrigado pela curtida! +1 crédito adicionado! 🎉")
        st.rerun()


st.sidebar.header("🔍 Localização do Terreno")

tipo_busca = st.sidebar.radio(
    "Método de Pesquisa:", ["Por Endereço", "Por Coordenadas GPS"]
)

if tipo_busca == "Por Endereço":
    endereco_input = st.sidebar.text_input(
        "Endereço em Joinville:",
        placeholder="Ex: Rua XV de Novembro, 1000, Centro",
    )

    if st.sidebar.button("Buscar e Consultar Viabilidade"):
        if endereco_input:
            geolocator = Nominatim(user_agent="proptech_joinville")
            try:
                busca_full = f"{endereco_input}, Joinville, Santa Catarina, Brasil"
                location = geolocator.geocode(busca_full)

                if location:
                    st.session_state.lat = location.latitude
                    st.session_state.lng = location.longitude
                    st.session_state.consultado = True
                    st.sidebar.success(
                        f"📍 Encontrado: {location.latitude:.5f}, {location.longitude:.5f}"
                    )
                else:
                    st.sidebar.error("Endereço não localizado.")
            except Exception as e:
                st.sidebar.error(f"Erro no serviço de geocodificação: {e}")
        else:
            st.sidebar.warning("Insira um endereço válido.")
else:
    lat_input = st.sidebar.number_input(
        "Latitude", value=st.session_state.lat, format="%.6f"
    )
    lng_input = st.sidebar.number_input(
        "Longitude", value=st.session_state.lng, format="%.6f"
    )

    if st.sidebar.button("Consultar Coordenadas"):
        st.session_state.lat = lat_input
        st.session_state.lng = lng_input
        st.session_state.consultado = True

st.sidebar.markdown("---")
st.sidebar.header("📐 Dimensões e Premissas")

st.session_state.area_terreno = st.sidebar.number_input(
    "Área do Terreno (m²)",
    value=st.session_state.area_terreno,
    min_value=1.0,
    step=50.0,
)

st.session_state.eficiencia = st.sidebar.slider(
    "Eficiência Vendável (%)",
    min_value=50.0,
    max_value=90.0,
    value=st.session_state.eficiencia,
    step=1.0,
)

st.session_state.valor_m2 = st.sidebar.number_input(
    "Preço Médio de Venda (R$/m²)",
    value=st.session_state.valor_m2,
    min_value=0.0,
    step=250.0,
)

renderizar_painel_monetizacao()


# ============================================================
# 5. PAINEL PRINCIPAL & PROCESSAMENTO
# ============================================================

if st.session_state.consultado:

    # Ponto e projeção de coordenadas
    ponto = Point(st.session_state.lng, st.session_state.lat)
    ponto_gdf = gpd.GeoDataFrame([{"geometry": ponto}], crs="EPSG:4326")
    ponto_gdf = ponto_gdf.to_crs(gdf_zoneamento.crs)

    # Cruzamento espacial
    resultado = gpd.sjoin(
        ponto_gdf, gdf_zoneamento, how="inner", predicate="intersects"
    )

    col_mapa, col_relatorio = st.columns([1, 1])

    # MAPA FOLIUM
    with col_mapa:
        st.subheader("🗺️ Localização e Zoneamento")

        m = folium.Map(
            location=[st.session_state.lat, st.session_state.lng], zoom_start=16
        )

        if not resultado.empty:
            try:
                indice_poligono = resultado.iloc[0]["index_right"]
                zona_selecionada = gdf_zoneamento.loc[[indice_poligono]].copy()
                zona_selecionada = zona_selecionada.to_crs("EPSG:4326")

                sigla_mapa = resultado.iloc[0]["sigla_z"]
                geometria = zona_selecionada.geometry.iloc[0]

                if geometria is not None and not geometria.is_empty:
                    geojson_data = geometria.__geo_interface__
                    folium.GeoJson(
                        data=geojson_data,
                        name=f"Zona {sigla_mapa}",
                        style_function=lambda feature: {
                            "fillColor": "#3388ff",
                            "color": "#0055cc",
                            "weight": 3,
                            "fillOpacity": 0.20,
                        },
                    ).add_to(m)
            except Exception as e:
                st.warning(
                    f"O zoneamento foi identificado, mas não foi possível desenhar o polígono. Erro: {e}"
                )

        folium.Marker(
            [st.session_state.lat, st.session_state.lng],
            popup="Terreno Consultado",
            tooltip="Terreno consultado",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width=500, height=420, key="mapa_folium")

    # RELATÓRIO E ABAS
    with col_relatorio:
        st.subheader("📋 Relatório Construtivo & Financeiro")

        if not resultado.empty:
            sigla = resultado.iloc[0]["sigla_z"]
            regra = df_louos[df_louos["sigla_z"] == sigla]

            if not regra.empty:
                info = regra.iloc[0]
                area = st.session_state.area_terreno
                valor_m2 = st.session_state.valor_m2
                eficiencia = st.session_state.eficiencia

                # Cálculos de Potencial
                area_projecao = area * info["taxa_ocupacao"]
                area_const_basica = area * info["ca_basico"]
                area_const_maxima = area * info["ca_maximo"]
                outorga_potencial_m2 = area_const_maxima - area_const_basica

                # Cálculos Privativos e Financeiros
                area_privativa_basica = area_const_basica * (eficiencia / 100)
                area_privativa_maxima = area_const_maxima * (eficiencia / 100)
                vgv_basico = area_privativa_basica * valor_m2
                vgv_maximo = area_privativa_maxima * valor_m2

                st.success(
                    f"**Zona Urbana:** {info['nome_zona']} ({info['sigla_z']})"
                )

                aba1, aba2, aba3, aba4 = st.tabs([
                    "📊 Índices Urbanísticos",
                    "🏗️ Estudo de Massa",
                    "💰 Simulação de VGV",
                    "📄 Exportação",
                ])

                # ABA 1: INDICES URBANÍSTICOS
                with aba1:
                    m1, m2 = st.columns(2)
                    m1.metric("C.A. Básico", info["ca_basico"])
                    m2.metric("C.A. Máximo", info["ca_maximo"])

                    m3, m4 = st.columns(2)
                    m3.metric(
                        "Taxa de Ocupação", f"{int(info['taxa_ocupacao'] * 100)}%"
                    )
                    m4.metric("Gabarito Máximo", f"{info['gabarito_max_pav']} pavs")

                    st.info(
                        f"📏 **Recuo Frontal Mínimo:** {info['recuo_frontal_m']} metros"
                    )

                # ABA 2: ESTUDO DE MASSA
                with aba2:
                    p1, p2, p3 = st.columns(3)
                    p1.metric("Projeção Solo", f"{area_projecao:.1f} m²")
                    p2.metric("Área Básica", f"{area_const_basica:.1f} m²")
                    p3.metric("Área Máxima", f"{area_const_maxima:.1f} m²")

                    st.markdown("---")
                    st.markdown(
                        f"💡 **Potencial Construtivo Adicional:** `{outorga_potencial_m2:.1f} m²`"
                    )

                    with st.expander("🔎 Como este resultado foi calculado?"):
                        st.write(f"""
                        - **Projeção no Solo:** {area:.2f} m² (Área do lote) × {info['taxa_ocupacao']*100}% (T.O.) = **{area_projecao:.2f} m²**
                        - **Área Construtiva Básica:** {area:.2f} m² × {info['ca_basico']} (C.A. Básico) = **{area_const_basica:.2f} m²**
                        - **Área Construtiva Máxima:** {area:.2f} m² × {info['ca_maximo']} (C.A. Máximo) = **{area_const_maxima:.2f} m²**
                        """)

                # ABA 3: SIMULAÇÃO DE VGV
                with aba3:
                    v1, v2 = st.columns(2)
                    v1.metric(
                        "Área Privativa Básica",
                        f"{area_privativa_basica:.1f} m²",
                        help="Calculada aplicando a taxa de eficiência sobre a área computável básica.",
                    )
                    v2.metric(
                        "Área Privativa Máxima",
                        f"{area_privativa_maxima:.1f} m²",
                        help="Calculada aplicando a taxa de eficiência sobre a área computável máxima.",
                    )

                    st.markdown("---")
                    v3, v4 = st.columns(2)
                    v3.metric("VGV Potencial Básico", f"R$ {vgv_basico:,.2f}")
                    v4.metric("VGV Potencial Máximo", f"R$ {vgv_maximo:,.2f}")

                # ABA 4: EXPORTAÇÃO E MONETIZAÇÃO
                with aba4:
                    st.markdown("### 📥 Download do Laudo de Viabilidade")
                    st.write(
                        "O laudo executivo reúne todos os índices normativos, limites computáveis e projeção financeira em um PDF pronto para apresentação."
                    )

                    if st.session_state["creditos_disponiveis"] > 0:
                        pdf_bytes = gerar_pdf(
                            info,
                            st.session_state.lat,
                            st.session_state.lng,
                            area,
                            area_projecao,
                            area_const_basica,
                            area_const_maxima,
                            outorga_potencial_m2,
                            eficiencia,
                            area_privativa_basica,
                            area_privativa_maxima,
                            valor_m2,
                            vgv_basico,
                            vgv_maximo,
                        )

                        if st.download_button(
                            label="📄 Baixar Relatório Completo (Consome 1 Crédito)",
                            data=pdf_bytes,
                            file_name=f"Laudo_Viabilidade_Joinville_{sigla}.pdf",
                            mime="application/pdf",
                            type="primary",
                        ):
                            st.session_state["creditos_disponiveis"] -= 1
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ Você não possui créditos suficientes para baixar o laudo em PDF."
                        )
                        st.info(
                            "👍 Clique no botão de curtida na barra lateral para ganhar créditos!"
                        )

            else:
                st.error(
                    f"Zona `{sigla}` encontrada no mapa, porém sem parâmetros cadastrados no arquivo `parametros_louos.csv`."
                )
        else:
            st.warning(
                "O ponto selecionado está fora dos limites de zoneamento cadastrados."
            )