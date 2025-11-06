# 🎬 IMDb Analytics Dashboard

Dashboard interactivo de análisis de películas y series usando datos públicos de IMDb. Proyecto académico de visualización de datos sobre la industria audiovisual.

## 📊 Características

- **Análisis temporal**: Evolución de la producción audiovisual desde 1950
- **Géneros**: Tendencias y popularidad de géneros cinematográficos
- **Personas**: Top directores y actores más prolíficos y mejor valorados
- **Geografía**: Análisis de producción por países
- **Series**: Estructura de temporadas y episodios

## 🚀 Tecnologías

- **Backend**: Python 3.9+
- **ETL**: DuckDB (procesamiento eficiente de archivos grandes)
- **Visualización**: Streamlit + Plotly
- **Datos**: IMDb Public Datasets
- **Formato**: Parquet (compresión ZSTD)

## 📁 Estructura del proyecto

```
imdb-dashboard/
├── app.py                      # Aplicación Streamlit
├── etl_imdb.py                 # Pipeline ETL con DuckDB
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── data_raw/                   # Archivos originales de IMDb (local, no en Git)
│   ├── title.basics.tsv.gz
│   ├── title.ratings.tsv.gz
│   ├── title.crew.tsv.gz
│   ├── title.principals.tsv.gz
│   ├── name.basics.tsv.gz
│   ├── title.akas.tsv.gz
│   └── title.episode.tsv.gz
└── data_processed/             # Archivos procesados (en Git)
    ├── titles_clean.parquet
    ├── genres_by_year.parquet
    ├── directors.parquet
    ├── actors.parquet
    ├── countries.parquet
    └── episodes.parquet
```

## 🔧 Instalación y uso local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/imdb-dashboard.git
cd imdb-dashboard
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Descargar datos de IMDb (opcional, si quieres regenerar los datasets)

```bash
mkdir data_raw
cd data_raw

# Descargar archivos desde https://datasets.imdbws.com/
wget https://datasets.imdbws.com/title.basics.tsv.gz
wget https://datasets.imdbws.com/title.ratings.tsv.gz
wget https://datasets.imdbws.com/title.crew.tsv.gz
wget https://datasets.imdbws.com/title.principals.tsv.gz
wget https://datasets.imdbws.com/name.basics.tsv.gz
wget https://datasets.imdbws.com/title.akas.tsv.gz
wget https://datasets.imdbws.com/title.episode.tsv.gz

cd ..
```

### 4. (Opcional) Ejecutar el pipeline ETL

Si descargaste los datos originales y quieres regenerarlos:

```bash
python etl_imdb.py
```

Este proceso puede tomar entre 10-30 minutos dependiendo de tu hardware. Generará los archivos `.parquet` optimizados en `data_processed/`.

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## ☁️ Deployment en Streamlit Cloud

### Requisitos previos

1. Cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
2. Repositorio en GitHub con los archivos `.parquet` procesados

### Pasos

1. **Subir el código a GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Configurar en Streamlit Cloud**:
   - Ve a [share.streamlit.io](https://share.streamlit.io)
   - Click en "New app"
   - Selecciona tu repositorio
   - Main file: `app.py`
   - Click en "Deploy"

3. **Importante**: Asegúrate de que los archivos `.parquet` estén en el repositorio dentro de la carpeta `data_processed/`

## 📊 Datasets procesados

Los archivos Parquet incluyen:

### `titles_clean.parquet`
Títulos principales con ratings filtrados (mínimo 1000 votos, años 1950-2024)

**Columnas**: 
- `tconst`, `titleType`, `primaryTitle`, `originalTitle`
- `startYear`, `endYear`, `runtimeMinutes`, `genres`
- `averageRating`, `numVotes`

### `genres_by_year.parquet`
Agregación de géneros por año

**Columnas**: 
- `startYear`, `genre`, `titleType`
- `count`, `avg_rating`, `total_votes`

### `directors.parquet`
Relación directores-títulos

**Columnas**: 
- `tconst`, `nconst`, `directorName`
- `primaryTitle`, `startYear`, `titleType`
- `averageRating`, `numVotes`

### `actors.parquet`
Relación actores-títulos (top 5 por título)

**Columnas**: 
- `tconst`, `nconst`, `actorName`, `category`, `ordering`
- `primaryTitle`, `startYear`, `titleType`
- `averageRating`, `numVotes`

### `countries.parquet`
Producción por país

**Columnas**: 
- `tconst`, `region` (código ISO)
- `primaryTitle`, `startYear`, `titleType`, `genres`
- `averageRating`, `numVotes`

### `episodes.parquet`
Estructura de series y episodios

**Columnas**: 
- `episodeId`, `seriesId`, `seasonNumber`, `episodeNumber`
- `episodeTitle`, `episodeYear`, `episodeRating`, `episodeVotes`
- `seriesTitle`, `seriesStartYear`

## 🎯 Filtros aplicados en el ETL

- **Años**: 1950-2024
- **Votos mínimos**: 1,000
- **Contenido adulto**: Excluido (`isAdult = 0`)
- **Tipos de contenido**: movie, tvSeries, tvMovie, tvEpisode, tvMiniSeries
- **Actores**: Solo los 5 principales por título

## 📈 Optimizaciones

- **DuckDB**: Procesamiento 10-20x más rápido que pandas puro
- **Parquet + ZSTD**: Compresión eficiente (reducción ~70% vs CSV)
- **Filtrado temprano**: Reducción de datos antes de joins
- **Lazy loading**: Streamlit carga solo los datos necesarios

## 🔍 Ejemplo de uso del ETL

```python
import duckdb

# Conectar
con = duckdb.connect()

# Query de ejemplo
result = con.execute("""
    SELECT 
        startYear,
        COUNT(*) as num_movies
    FROM read_parquet('data_processed/titles_clean.parquet')
    WHERE titleType = 'movie'
    GROUP BY startYear
    ORDER BY startYear
""").df()

print(result)
```

## 📝 Notas importantes

### Para desarrollo local

1. Los archivos originales de IMDb (`data_raw/`) **NO** deben subirse a Git
2. Añade `data_raw/` a `.gitignore`
3. Solo sube los archivos procesados (`data_processed/*.parquet`)

### Limitaciones de tamaño

- GitHub: 100 MB por archivo
- Streamlit Cloud (free tier): ~1 GB RAM
- Si los archivos superan estos límites, considera:
  - Filtros más agresivos (más votos, menos años)
  - Split en múltiples archivos
  - Usar Git LFS para archivos grandes

## 🤝 Contribuciones

Este es un proyecto académico. Si encuentras errores o tienes sugerencias:

1. Abre un Issue
2. Envía un Pull Request

## 📄 Licencia

Este proyecto usa datos públicos de IMDb. Por favor, revisa las [condiciones de uso de IMDb](https://www.imdb.com/conditions).

## 🔗 Enlaces útiles

- [IMDb Datasets](https://datasets.imdbws.com/)
- [Documentación IMDb Datasets](https://www.imdb.com/interfaces/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [Plotly Python](https://plotly.com/python/)

## 📧 Contacto

Para preguntas sobre el proyecto, abre un Issue en GitHub.

---

**⚠️ Disclaimer**: Este dashboard es solo para fines educativos. Los datos pertenecen a IMDb y están sujetos a sus términos de uso.