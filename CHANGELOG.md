# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

O formato segue uma estrutura simples baseada em versionamento semântico:

- **MAJOR**: mudanças grandes ou incompatíveis
- **MINOR**: novas funcionalidades compatíveis
- **PATCH**: correções e pequenos ajustes

## [1.1.0] - 2026-09-30

### Adicionado
- Exibição da versão atual do sistema na barra lateral.
- Histórico de versões dentro do portal.

### Corrigido
- Carregamento da camada correta de zoneamento.
- Validação do CRS do shapefile.
- Conversão da camada para EPSG:4326 para visualização.
- Uso de EPSG:31982 para operações métricas.
- Buffer espacial de 20 metros para melhorar a identificação de zoneamento.

### Melhorado
- Identificação espacial das zonas urbanas.
- Organização do código de carregamento de dados.
- Tratamento de geometrias inválidas.

## [1.0.0]

### Adicionado
- Consulta por endereço.
- Consulta por latitude e longitude.
- Identificação automática do zoneamento urbano.
- Consulta de parâmetros urbanísticos da LOUOS.
- Cálculo de coeficiente de aproveitamento.
- Cálculo de taxa de ocupação.
- Exibição de gabarito máximo e recuo frontal.
- Estudo de massa.
- Cálculo de área construtiva básica e máxima.
- Estimativa de potencial construtivo adicional.
- Simulação de VGV.
- Geração de relatório em PDF.
- Visualização geográfica com Folium.
