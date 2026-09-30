                st.success(
                    f"**Zona Urbana:** {info['nome_zona']} ({info['sigla_z']})"
                )

                aba1, aba2, aba3, aba4 = st.tabs([
                    "📊 Índices Urbanísticos",
                    "🏗️ Estudo de Massa",
                    "💰 Simulação de VGV",
                    "📄 Exportação",
                ])

                # ABA 1: ÍNDICES URBANÍSTICOS
                with aba1:
                    m1, m2 = st.columns(2)
                    m1.metric("C.A. Básico", formatar_numero(info["ca_basico"], 2))
                    m2.metric("C.A. Máximo", formatar_numero(info["ca_maximo"], 2))

                    m3, m4 = st.columns(2)
                    m3.metric(
                        "Taxa de Ocupação", f"{int(info['taxa_ocupacao'] * 100)}%"
                    )
                    m4.metric("Gabarito Máximo", f"{info['gabarito_max_pav']} pavs")

                    st.info(
                        f"📏 **Recuo Frontal Mínimo:** {formatar_numero(info['recuo_frontal_m'], 1)} metros"
                    )

                # ABA 2: ESTUDO DE MASSA
                with aba2:
                    p1, p2, p3 = st.columns(3)
                    p1.metric("Projeção Solo", f"{formatar_numero(area_projecao, 1)} m²")
                    p2.metric("Área Básica", f"{formatar_numero(area_const_basica, 1)} m²")
                    p3.metric("Área Máxima", f"{formatar_numero(area_const_maxima, 1)} m²")

                    st.markdown("---")
                    st.markdown(
                        f"💡 **Potencial Construtivo Adicional:** `{formatar_numero(outorga_potencial_m2, 1)} m²`"
                    )

                    with st.expander("🔎 Como este resultado foi calculated?"):
                        st.write(f"""
                        - **Projeção no Solo:** {formatar_numero(area, 2)} m² × {int(info['taxa_ocupacao']*100)}% (T.O.) = **{formatar_numero(area_projecao, 2)} m²**
                        - **Área Construtiva Básica:** {formatar_numero(area, 2)} m² × {formatar_numero(info['ca_basico'], 2)} (C.A. Básico) = **{formatar_numero(area_const_basica, 2)} m²**
                        - **Área Construtiva Máxima:** {formatar_numero(area, 2)} m² × {formatar_numero(info['ca_maximo'], 2)} (C.A. Máximo) = **{formatar_numero(area_const_maxima, 2)} m²**
                        """)

                # ABA 3: SIMULAÇÃO DE VGV
                with aba3:
                    v1, v2 = st.columns(2)
                    v1.metric(
                        "Área Privativa Básica",
                        f"{formatar_numero(area_privativa_basica, 1)} m²",
                        help="Calculada aplicando a taxa de eficiência sobre a área computável básica.",
                    )
                    v2.metric(
                        "Área Privativa Máxima",
                        f"{formatar_numero(area_privativa_maxima, 1)} m²",
                        help="Calculada aplicando a taxa de eficiência sobre a área computável máxima.",
                    )

                    st.markdown("---")
                    v3, v4 = st.columns(2)
                    v3.metric("VGV Potencial Básico", formatar_moeda(vgv_basico))
                    v4.metric("VGV Potencial Máximo", formatar_moeda(vgv_maximo))

                # ABA 4: EXPORTAÇÃO E MONETIZAÇÃO
                with aba4:
                    st.markdown("### 📥 Download do Laudo de Viabilidade")
                    st.write(
                        "O laudo executivo reúne todos os índices normativos, limites computáveis e projeção financeira em um PDF pronto para apresentação."
                    )

                    if st.session_state["creditos_disponiveis"] > 0:
                        pdf_bytes = gerar_pdf(
                            info,
                            st.session_state["lat"],
                            st.session_state["lng"],
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
            st.error(
                "Não foi possível identificar o zoneamento deste ponto. "
                "O local pode estar fora da área mapeada ou muito próximo ao limite "
                "da camada de zoneamento."
            )
            with st.expander("🔎 Diagnóstico técnico"):
                st.write(
                    f"Coordenada consultada: {st.session_state['lat']:.6f}, "
                    f"{st.session_state['lng']:.6f}"
                )
                st.write(f"CRS da camada: {gdf_zoneamento.crs}")
                st.write(f"Quantidade de polígonos: {len(gdf_zoneamento)}")
                st.write(f"Limites da camada: {gdf_zoneamento.total_bounds.tolist()}")