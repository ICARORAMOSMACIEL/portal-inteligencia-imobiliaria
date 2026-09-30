from dataclasses import replace
from datetime import date, timedelta
import unittest

import pandas as pd

from comparador_precos import (
    Consulta, base_demonstracao, base_vazia, comparar, deduplicar,
    exportar_csv, ler_csv, numero, relatorio_html, url_canonica, validar_base,
)


HOJE = date(2026, 9, 24)


class ComparadorTests(unittest.TestCase):
    def setUp(self):
        self.base = base_demonstracao(HOJE)
        self.alvo = Consulta("Costa e Silva", 500, 500000, "SA-02", "Plano",
                             "Sem restrições identificadas", demonstracao=True)

    def test_calculo_da_faixa_e_classificacao(self):
        r = comparar(self.base, self.alvo, HOJE)
        self.assertEqual(r["n"], 8)
        self.assertEqual(r["mediana_m2"], 870)
        self.assertEqual(r["faixa_inferior"], 417500)
        self.assertEqual(r["faixa_superior"], 452500)
        self.assertEqual(r["status"], "Acima da faixa dos comparáveis")
        self.assertAlmostEqual(r["diferenca_pct"], (1000/870 - 1)*100)
        for preco, label in [(400000, "Abaixo"), (417500, "Dentro"), (452500, "Dentro")]:
            self.assertTrue(comparar(self.base, replace(self.alvo, preco_anunciado=preco), HOJE)["status"].startswith(label))

    def test_dados_insuficientes_nao_inventam_valores(self):
        for dados in (base_vazia(), self.base.head(4)):
            r = comparar(dados, self.alvo, HOJE)
            self.assertEqual(r["status"], "Dados insuficientes")
            self.assertIsNone(r["mediana_m2"])
            self.assertIsNone(r["diferenca_pct"])

    def test_filtros_de_comparabilidade_e_atualidade(self):
        for campo, valor in [("bairro", "Centro"), ("sigla_z", "SA-03"), ("topografia", "Declive"),
                             ("area_m2", 2000), ("restricoes", "Com restrições"), ("status", "Vendido"),
                             ("data_verificacao", (HOJE-timedelta(days=181)).isoformat())]:
            dados = self.base.copy()
            dados.loc[0, campo] = valor
            self.assertEqual(comparar(dados, self.alvo, HOJE)["n"], 7, campo)
        r = comparar(self.base, replace(self.alvo, bairro=" costa E silva ", sigla_z="sa-02"), HOJE)
        self.assertEqual(r["n"], 8)

    def test_atualizacao_de_vendido_nao_ressuscita_anuncio_antigo(self):
        antiga = self.base.iloc[[0]].copy()
        antiga["data_verificacao"] = (HOJE-timedelta(days=1)).isoformat()
        recente = self.base.iloc[[0]].copy()
        recente["status"] = "Vendido"
        recente["url"] = "https://example.com/outro-anunciante"
        dados = pd.concat([antiga, self.base.iloc[1:], recente], ignore_index=True)
        self.assertEqual(len(deduplicar(dados)), 8)
        self.assertEqual(comparar(dados, self.alvo, HOJE)["n"], 7)

    def test_url_duplicada_e_exclusao_transitiva_do_proprio_terreno(self):
        copia = self.base.iloc[[0]].copy()
        copia["referencia_lote"] = "ID-DIFERENTE"
        copia["url"] = copia.url + "?utm_source=teste#foto"
        dados = pd.concat([self.base, copia], ignore_index=True)
        self.assertEqual(comparar(dados, self.alvo, HOJE)["n"], 8)
        r = comparar(dados, replace(self.alvo, referencia_lote="FICTICIO-01"), HOJE)
        self.assertEqual(r["n"], 7)
        r = comparar(dados, replace(self.alvo, url=self.base.iloc[0].url), HOJE)
        self.assertEqual(r["n"], 7)
        self.assertNotEqual(url_canonica("https://x.com/anuncio?id=1"), url_canonica("https://x.com/anuncio?id=2"))

    def test_demonstracao_nao_contamina_base_real(self):
        r = comparar(self.base, replace(self.alvo, demonstracao=False), HOJE)
        self.assertEqual(r["n"], 0)
        self.assertIsNone(r["mediana_m2"])
        r = comparar(self.base, self.alvo, HOJE)
        self.assertIn("DADOS FICTÍCIOS", relatorio_html(r).decode())

    def test_restricoes_e_dispersao_impedem_classificacao(self):
        for campo, valor in [("topografia", "Não verificada"), ("restricoes", "Não verificadas"), ("restricoes", "Com restrições")]:
            r = comparar(self.base, replace(self.alvo, **{campo: valor}), HOJE)
            self.assertIsNone(r["mediana_m2"])
        dados = self.base.copy()
        dados["preco_anunciado"] = dados.area_m2 * pd.Series([100, 200, 300, 400, 2000, 4000, 8000, 16000])
        self.assertEqual(comparar(dados, self.alvo, HOJE)["status"], "Amostra heterogênea")

    def test_numeros_brasileiros_e_csv_exportado_voltam_iguais(self):
        self.assertEqual(numero("R$ 450.000,50"), 450000.50)
        self.assertEqual(numero("500,25"), 500.25)
        carregada, erros = validar_base(ler_csv(exportar_csv(self.base)), HOJE)
        self.assertTrue(erros.empty)
        self.assertEqual(comparar(carregada, self.alvo, HOJE)["mediana_m2"], 870)

    def test_linhas_invalidas_sao_identificadas(self):
        for campo, valor in [("area_m2", 0), ("preco_anunciado", "inf"), ("url", "javascript:alert(1)"),
                             ("data_verificacao", "2027-01-01"), ("cidade", "Curitiba"), ("tipo", "Casa")]:
            dados = self.base.copy()
            dados[campo] = dados[campo].astype(object)
            dados.loc[0, campo] = valor
            validos, erros = validar_base(dados, HOJE)
            self.assertEqual(len(validos), 7, campo)
            self.assertEqual(len(erros), 1, campo)
        for invalido in [0, -10, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                comparar(self.base, replace(self.alvo, area_m2=invalido), HOJE)

    def test_relatorio_escapa_texto_e_csv_nao_executa_formula(self):
        dados = self.base.copy()
        dados.loc[0, "fonte"] = '<script>alert("x")</script>'
        r = comparar(dados, self.alvo, HOJE)
        html = relatorio_html(r).decode()
        self.assertNotIn('<script>alert', html)
        self.assertIn('&lt;script&gt;', html)
        dados.loc[0, "fonte"] = '=HYPERLINK("https://example.com")'
        self.assertIn("'=HYPERLINK", exportar_csv(dados).decode("utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
