import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# 1. Carregar a camada do SIMGeo e a tabela de parâmetros da LOUOS
shapefile_path = "Data/zoneamento/anexos_II_III.shp"
gdf = gpd.read_file(shapefile_path)
df_louos = pd.read_csv("Data/parametros_louos.csv")

# 2. Definir coordenada de teste em Joinville
latitude = -26.2745
longitude = -48.8512
ponto = Point(longitude, latitude)

# 3. Ajustar projeção espacial
ponto_gdf = gpd.GeoDataFrame([{'geometry': ponto}], crs="EPSG:4326").to_crs(gdf.crs)

# 4. Interseção Espacial (SIMGeo)
resultado = gpd.sjoin(ponto_gdf, gdf, how="inner", predicate="intersects")

if not resultado.empty:
    sigla = resultado.iloc[0]['sigla_z']
    
    # 5. Cruzamento com o CSV da LOUOS (JOIN)
    regra = df_louos[df_louos['sigla_z'] == sigla]
    
    if not regra.empty:
        info = regra.iloc[0]
        print("\n==========================================")
        print("🏢 RELATÓRIO PRELIMINAR DE VIABILIDADE")
        print("==========================================")
        print(f"• Zona Identificada: {info['nome_zona']} ({info['sigla_z']})")
        print(f"• Coeficiente de Aproveitamento Básico: {info['ca_basico']}")
        print(f"• Coeficiente de Aproveitamento Máximo: {info['ca_maximo']}")
        print(f"• Taxa de Ocupação Máxima: {int(info['taxa_ocupacao'] * 100)}%")
        print(f"• Gabarito Máximo Permitido: {info['gabarito_max_pav']} pavimentos")
        print(f"• Recuo Frontal Mínimo: {info['recuo_frontal_m']}m")
        print("==========================================\n")
    else:
        print(f"\n⚠️ Zona {sigla} encontrada no SIMGeo, mas não cadastrada no CSV de parâmetros.")