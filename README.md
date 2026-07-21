# World Cup 2026 Final Analysis

Análisis de datos del último partido del Mundial de Fútbol 2026: **Argentina vs España** (19 julio 2026, MetLife Stadium).

**Resultado**: España 1 - 0 Argentina (t.e.) | Gol: Ferran Torres 106'

## Fuentes de datos

| Fuente | Tipo | Descripción |
|--------|------|-------------|
| [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json) | JSON estático | Resultados, goleadores, grupos, sedes |
| [wcup2026.org](https://wcup2026.org/api/data.php) | REST API | Partidos, clasificaciones, datos del torneo |
| FotMob API | REST API (no oficial) | xG, stats detallados, formaciones, ratings |

## Estructura

```
├── config.yaml              # Configuración del proyecto
├── requirements.txt         # Dependencias Python
├── data/
│   ├── raw/                 # Datos crudos de APIs
│   └── processed/           # CSVs limpios
├── notebooks/
│   ├── 01_data_collection   # Fetch de datos
│   ├── 02_eda_analysis      # Análisis exploratorio
│   └── 03_visualizations    # Gráficos
├── src/
│   ├── openfootball_client  # Cliente openfootball
│   ├── wcup_client          # Cliente wcup2026
│   ├── clean.py            # Limpieza y transformación
│   ├── analyze.py           # Métricas y análisis
│   └── visualize.py         # Visualizaciones
└── tests/
```

## Uso

```bash
pip install -r requirements.txt
python -m src.pipeline
```

Luego abrir los notebooks:

```bash
jupyter notebook notebooks/
```

## Análisis incluidas

- Comparativa de camino a la final
- Línea de tiempo de goles
- Estadísticas del torneo
- Clasificaciones de grupos
- Mapas de tiro (cancha)
- [Futuro] xG, pases, formaciones
