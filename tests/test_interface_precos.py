"""Fluxos reais do Streamlit sem navegador e sem gravar referências no servidor."""
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def abrir_comparador():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio(key="pagina_portal").set_value("Comparar preços de terrenos").run()
    return app


class InterfaceTests(unittest.TestCase):
    def test_demo_e_volta_ao_simulador(self):
        app = abrir_comparador()
        self.assertFalse(app.exception)
        self.assertTrue(any("Ainda não há referências" in msg.value for msg in app.info))
        app.checkbox(key="precos_demo").check().run()
        next(b for b in app.button if b.label == "Comparar preço").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(t.value == "Acima da faixa dos comparáveis" for t in app.subheader))
        self.assertEqual(app.metric[1].value, "R$ 870,00")
        self.assertEqual(app.metric[2].value, "+14,9%")
        app.checkbox(key="precos_demo").uncheck().run()
        self.assertEqual(len(app.metric), 0)
        self.assertEqual(len(app.session_state["precos_base"]), 0)
        app.radio(key="pagina_portal").set_value("Viabilidade construtiva").run()
        self.assertFalse(app.exception)

    def test_cadastro_na_sessao_e_base_de_outro_visitante(self):
        app = abrir_comparador()
        for key, valor in {"cad_ref": "TESTE-001", "cad_bairro": "Costa e Silva", "cad_zona": "SA-02",
                           "cad_fonte": "Teste automatizado", "cad_url": "https://example.org/teste"}.items():
            app.text_input(key=key).set_value(valor)
        app.number_input(key="cad_preco").set_value(450000.0)
        app.selectbox(key="cad_topo").set_value("Plano")
        app.selectbox(key="cad_restricoes").set_value("Sem restrições identificadas")
        next(b for b in app.button if b.label == "Adicionar à minha base").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["precos_base"]), 1)
        outro = abrir_comparador()
        self.assertFalse(outro.exception)
        self.assertEqual(len(outro.session_state["precos_base"]), 0)


if __name__ == "__main__":
    unittest.main()
