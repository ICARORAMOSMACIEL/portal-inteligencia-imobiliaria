import geopandas as gpd
import os

# Caminho para o arquivo Shapefile extraído
shapefile_path = "data/zoneamento/anexos_II_III.shp"

# 1. Verificar se o arquivo existe no diretório
if not os.path.exists(shapefile_path):
    print(f"❌ Arquivo não encontrado em: {shapefile_path}")
    print("Certifique-se de extrair o ZIP na pasta 'data/zoneamento/'.")
else:
    print("⏳ Carregando o arquivo Shapefile do SIMGeo...")
    
    # 2. Ler a camada vetorial com GeoPandas
    gdf = gpd.read_file(shapefile_path)
    
    print("\n✅ Camada de Zoneamento carregada com sucesso!")
    print(f"• Total de Polígonos/Zonas mapeadas: {len(gdf)}")
    print(f"• Sistema de Projeção (CRS): {gdf.crs}")
    
    # 3. Exibir os nomes das colunas (atributos)
    print("\n📋 Colunas disponíveis na tabela do SIMGeo:")
    print(list(gdf.columns))
    
    # 4. Mostrar as primeiras 5 linhas dos dados
    print("\n🔍 Amostra dos dados de zoneamento:")
    # Selecionamos apenas algumas colunas para facilitar a leitura no terminal
    cols_to_show = [col for col in gdf.columns if col != 'geometry'][:5]
    print(gdf[cols_to_show].head())