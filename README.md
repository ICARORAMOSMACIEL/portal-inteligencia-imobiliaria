# 🏢 Portal de Inteligência Imobiliária - Joinville/SC

Aplicação web desenvolvida em Python e Streamlit para análise preliminar de viabilidade construtiva e potencial imobiliário de terrenos em Joinville/SC.

O sistema utiliza dados geográficos de zoneamento urbano e parâmetros da LOUOS para identificar automaticamente a zona de um terreno e estimar seu potencial construtivo e financeiro.

## 🚀 Aplicação online

Acesse:
https://app-inteligencia-imobiliaria-iujkcagc5ujkam7f3tclaq.streamlit.app/

## 🎯 Objetivo do projeto

O projeto foi criado para facilitar a análise inicial de terrenos, permitindo consultar:

- Zoneamento urbano
- Coeficiente de aproveitamento
- Taxa de ocupação
- Gabarito máximo
- Recuo frontal
- Área construtiva básica
- Área construtiva máxima
- Potencial construtivo adicional
- Área privativa estimada
- VGV potencial

## 🗺️ Consulta por localização

O usuário pode pesquisar um terreno utilizando:

- Endereço
- Latitude e longitude

A aplicação converte o endereço em coordenadas geográficas e realiza um cruzamento espacial com os polígonos de zoneamento do município.

Exemplo de resultado:

```text
Zona Urbana:
Setor Adensável 03 (AUAP) (SA-03)
```

## 🏗️ Estudo de potencial construtivo

### Projeção máxima no solo

```text
Área do terreno × Taxa de Ocupação
```

### Área construtiva básica

```text
Área do terreno × C.A. Básico
```

### Área construtiva máxima

```text
Área do terreno × C.A. Máximo
```

### Potencial construtivo adicional

```text
Área Máxima - Área Básica
```

## 💰 Simulação de VGV

O sistema permite informar:

- Área do terreno
- Eficiência vendável
- Preço médio de venda por m²

Com essas informações são estimados:

- Área privativa básica
- Área privativa máxima
- VGV básico
- VGV máximo

## 📄 Relatório em PDF

A plataforma permite gerar um relatório de viabilidade contendo:

- Localização
- Zona urbana
- Parâmetros urbanísticos
- Potencial construtivo
- Estimativa de VGV

## 📊 Comparação de preços

O projeto também possui módulos voltados à comparação exploratória de preços anunciados de terrenos, com suporte para:

- Bairro
- Área do lote
- Preço anunciado
- Preço por m²
- Zoneamento
- Topografia
- Restrições
- Fonte do anúncio
- Data de verificação

## 🧰 Tecnologias utilizadas

- Python
- Streamlit
- GeoPandas
- Pandas
- Shapely
- Folium
- Streamlit Folium
- Geopy
- ReportLab
- Git
- GitHub

## 🌎 Geoprocessamento

A aplicação utiliza dados geográficos em formato Shapefile.

Para visualização e coordenadas geográficas:

```text
EPSG:4326
WGS 84
```

Para operações métricas, como buffer espacial:

```text
EPSG:31982
SIRGAS 2000 / UTM zona 22S
```

## 📂 Estrutura do projeto

```text
portal-inteligencia-imobiliaria/
│
├── app.py
├── comparador_precos.py
├── pagina_precos.py
├── README.md
├── requirements.txt
├── packages.txt
├── .gitignore
│
├── data/
│   ├── parametros_louos.csv
│   ├── shp_zoneamento.zip
│   ├── terrenos_mercado.csv
│   └── Zoneamento/
│
└── tests/
```

## ▶️ Como executar localmente

Clone o repositório:

```bash
git clone https://github.com/ICARORAMOSMACIEL/portal-inteligencia-imobiliaria.git
```

Entre na pasta:

```bash
cd portal-inteligencia-imobiliaria
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a aplicação:

```bash
streamlit run app.py
```

## 🔄 Fluxo da aplicação

```text
Usuário informa endereço
        ↓
Geocodificação
        ↓
Latitude / Longitude
        ↓
GeoPandas + Shapely
        ↓
Cruzamento com o zoneamento
        ↓
Identificação da zona
        ↓
Consulta dos parâmetros LOUOS
        ↓
Cálculo do potencial construtivo
        ↓
Simulação financeira / VGV
```

## 🔮 Próximas melhorias

- Comparação de terrenos
- Análise do valor do terreno
- Indicadores de preço por região
- Dashboard de bairros
- Histórico de consultas
- Score de oportunidade imobiliária
- Integração com novas bases públicas
- Melhorias na geração de relatórios

## ⚠️ Aviso

As informações apresentadas pela plataforma possuem caráter informativo e de apoio à análise preliminar.

Para decisões de compra, incorporação, construção ou aprovação de projetos, recomenda-se consultar os órgãos municipais competentes e profissionais habilitados.

## 👨‍💻 Autor

**Icaro Ramos Maciel**

LinkedIn:  
https://www.linkedin.com/in/icaroramosmaciel/

GitHub:  
https://github.com/ICARORAMOSMACIEL
