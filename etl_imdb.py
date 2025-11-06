"""
ETL Pipeline para procesar datasets de IMDb
Usa DuckDB para procesamiento eficiente de archivos grandes
Genera datasets optimizados en formato Parquet para Streamlit
"""

import duckdb
import pandas as pd
from pathlib import Path
import time

# Configuración
DATA_DIR = Path("data_raw")  # Donde están los .tsv.gz descargados
OUTPUT_DIR = Path("data_processed")  # Donde se guardarán los .parquet
OUTPUT_DIR.mkdir(exist_ok=True)

# Filtros
MIN_VOTES = 1000
START_YEAR = 1950
END_YEAR = 2024

print("🚀 Iniciando pipeline ETL de IMDb con DuckDB...")
start_time = time.time()

# Conectar a DuckDB (en memoria)
con = duckdb.connect()

# ============================================================================
# 1. TÍTULOS BASE (titles_clean.parquet)
# ============================================================================
print("\n📊 Procesando títulos principales...")

query_titles = f"""
    CREATE OR REPLACE TABLE titles_base AS
    SELECT 
        tconst,
        titleType,
        primaryTitle,
        originalTitle,
        isAdult,
        CAST(startYear AS INTEGER) as startYear,
        CAST(endYear AS INTEGER) as endYear,
        CAST(runtimeMinutes AS INTEGER) as runtimeMinutes,
        genres
    FROM read_csv_auto('{DATA_DIR}/title.basics.tsv.gz', 
                       delim='\t', 
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
    WHERE titleType IN ('movie', 'tvSeries', 'tvMovie', 'tvEpisode', 'tvMiniSeries')
        AND startYear >= {START_YEAR} 
        AND startYear <= {END_YEAR}
"""
con.execute(query_titles)
print(f"   ✓ Títulos filtrados: {con.execute('SELECT COUNT(*) FROM titles_base').fetchone()[0]:,}")

# ============================================================================
# 2. RATINGS (ratings.parquet)
# ============================================================================
print("\n⭐ Procesando ratings...")

query_ratings = f"""
    CREATE OR REPLACE TABLE ratings_filtered AS
    SELECT 
        r.tconst,
        CAST(r.averageRating AS FLOAT) as averageRating,
        CAST(r.numVotes AS INTEGER) as numVotes
    FROM read_csv_auto('{DATA_DIR}/title.ratings.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip') r
    WHERE r.numVotes >= {MIN_VOTES}
"""
con.execute(query_ratings)
print(f"   ✓ Ratings con mínimo {MIN_VOTES} votos: {con.execute('SELECT COUNT(*) FROM ratings_filtered').fetchone()[0]:,}")

# ============================================================================
# 3. JOIN TÍTULOS + RATINGS (titles_clean.parquet)
# ============================================================================
print("\n🔗 Uniendo títulos con ratings...")

query_join = """
    CREATE OR REPLACE TABLE titles_clean AS
    SELECT 
        t.tconst,
        t.titleType,
        t.primaryTitle,
        t.originalTitle,
        t.startYear,
        t.endYear,
        t.runtimeMinutes,
        t.genres,
        r.averageRating,
        r.numVotes
    FROM titles_base t
    INNER JOIN ratings_filtered r ON t.tconst = r.tconst
"""
con.execute(query_join)

# Exportar
con.execute(f"""
    COPY titles_clean TO '{OUTPUT_DIR}/titles_clean.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
titles_count = con.execute('SELECT COUNT(*) FROM titles_clean').fetchone()[0]
print(f"   ✓ Exportado: titles_clean.parquet ({titles_count:,} registros)")

# ============================================================================
# 4. GÉNEROS POR AÑO (genres_by_year.parquet)
# ============================================================================
print("\n🎬 Generando análisis de géneros por año...")

query_genres = """
    CREATE OR REPLACE TABLE genres_exploded AS
    SELECT 
        tconst,
        titleType,
        startYear,
        UNNEST(string_split(genres, ',')) as genre,
        averageRating,
        numVotes
    FROM titles_clean
    WHERE genres IS NOT NULL AND genres != ''
"""
con.execute(query_genres)

query_genres_agg = """
    CREATE OR REPLACE TABLE genres_by_year AS
    SELECT 
        startYear,
        genre,
        titleType,
        COUNT(*) as count,
        ROUND(AVG(averageRating), 2) as avg_rating,
        SUM(numVotes) as total_votes
    FROM genres_exploded
    GROUP BY startYear, genre, titleType
    ORDER BY startYear, genre, titleType
"""
con.execute(query_genres_agg)

con.execute(f"""
    COPY genres_by_year TO '{OUTPUT_DIR}/genres_by_year.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
print(f"   ✓ Exportado: genres_by_year.parquet")

# ============================================================================
# 5. DIRECTORES (directors.parquet)
# ============================================================================
print("\n🎥 Procesando directores...")

query_crew = f"""
    CREATE OR REPLACE TABLE crew_base AS
    SELECT 
        tconst,
        directors
    FROM read_csv_auto('{DATA_DIR}/title.crew.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
    WHERE directors IS NOT NULL AND directors != ''
"""
con.execute(query_crew)

query_directors = """
    CREATE OR REPLACE TABLE directors_exploded AS
    SELECT 
        c.tconst,
        UNNEST(string_split(c.directors, ',')) as nconst
    FROM crew_base c
    INNER JOIN titles_clean t ON c.tconst = t.tconst
"""
con.execute(query_directors)

query_people = f"""
    CREATE OR REPLACE TABLE people_base AS
    SELECT 
        nconst,
        primaryName,
        CAST(birthYear AS INTEGER) as birthYear,
        CAST(deathYear AS INTEGER) as deathYear,
        primaryProfession
    FROM read_csv_auto('{DATA_DIR}/name.basics.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
"""
con.execute(query_people)

query_directors_final = """
    CREATE OR REPLACE TABLE directors AS
    SELECT 
        d.tconst,
        d.nconst,
        p.primaryName as directorName,
        t.primaryTitle,
        t.startYear,
        t.titleType,
        t.averageRating,
        t.numVotes
    FROM directors_exploded d
    INNER JOIN people_base p ON d.nconst = p.nconst
    INNER JOIN titles_clean t ON d.tconst = t.tconst
"""
con.execute(query_directors_final)

con.execute(f"""
    COPY directors TO '{OUTPUT_DIR}/directors.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
directors_count = con.execute('SELECT COUNT(*) FROM directors').fetchone()[0]
print(f"   ✓ Exportado: directors.parquet ({directors_count:,} registros)")

# ============================================================================
# 6. ACTORES (actors.parquet)
# ============================================================================
print("\n🎭 Procesando actores principales...")

query_principals = f"""
    CREATE OR REPLACE TABLE principals_base AS
    SELECT 
        tconst,
        nconst,
        category,
        CAST(ordering AS INTEGER) as ordering
    FROM read_csv_auto('{DATA_DIR}/title.principals.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
    WHERE category IN ('actor', 'actress')
        AND ordering <= 5
"""
con.execute(query_principals)

query_actors_final = """
    CREATE OR REPLACE TABLE actors AS
    SELECT 
        pr.tconst,
        pr.nconst,
        p.primaryName as actorName,
        pr.category,
        pr.ordering,
        t.primaryTitle,
        t.startYear,
        t.titleType,
        t.averageRating,
        t.numVotes
    FROM principals_base pr
    INNER JOIN people_base p ON pr.nconst = p.nconst
    INNER JOIN titles_clean t ON pr.tconst = t.tconst
"""
con.execute(query_actors_final)

con.execute(f"""
    COPY actors TO '{OUTPUT_DIR}/actors.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
actors_count = con.execute('SELECT COUNT(*) FROM actors').fetchone()[0]
print(f"   ✓ Exportado: actors.parquet ({actors_count:,} registros)")

# ============================================================================
# 7. PAÍSES (akas para región)
# ============================================================================
print("\n🌍 Procesando información de países...")

query_akas = f"""
    CREATE OR REPLACE TABLE countries_base AS
    SELECT DISTINCT
        titleId as tconst,
        region
    FROM read_csv_auto('{DATA_DIR}/title.akas.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
    WHERE region IS NOT NULL 
        AND region != ''
        AND length(region) = 2
"""
con.execute(query_akas)

query_countries = """
    CREATE OR REPLACE TABLE countries AS
    SELECT 
        a.tconst,
        a.region,
        t.primaryTitle,
        t.startYear,
        t.titleType,
        t.genres,
        t.averageRating,
        t.numVotes
    FROM countries_base a
    INNER JOIN titles_clean t ON a.tconst = t.tconst
"""
con.execute(query_countries)

con.execute(f"""
    COPY countries TO '{OUTPUT_DIR}/countries.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
print(f"   ✓ Exportado: countries.parquet")

# ============================================================================
# 8. ESTRUCTURA DE EPISODIOS (episodes.parquet)
# ============================================================================
print("\n📺 Procesando estructura de series (episodios)...")

query_episodes = f"""
    CREATE OR REPLACE TABLE episodes_base AS
    SELECT 
        tconst,
        parentTconst,
        CAST(seasonNumber AS INTEGER) as seasonNumber,
        CAST(episodeNumber AS INTEGER) as episodeNumber
    FROM read_csv_auto('{DATA_DIR}/title.episode.tsv.gz',
                       delim='\t',
                       header=true,
                       nullstr='\\N',
                       compression='gzip')
    WHERE seasonNumber IS NOT NULL 
        AND episodeNumber IS NOT NULL
"""
con.execute(query_episodes)

query_episodes_final = """
    CREATE OR REPLACE TABLE episodes AS
    SELECT 
        e.tconst as episodeId,
        e.parentTconst as seriesId,
        e.seasonNumber,
        e.episodeNumber,
        t.primaryTitle as episodeTitle,
        t.startYear as episodeYear,
        t.averageRating as episodeRating,
        t.numVotes as episodeVotes,
        ts.primaryTitle as seriesTitle,
        ts.startYear as seriesStartYear
    FROM episodes_base e
    INNER JOIN titles_clean t ON e.tconst = t.tconst
    INNER JOIN titles_clean ts ON e.parentTconst = ts.tconst
    WHERE ts.titleType IN ('tvSeries', 'tvMiniSeries')
"""
con.execute(query_episodes_final)

con.execute(f"""
    COPY episodes TO '{OUTPUT_DIR}/episodes.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
episodes_count = con.execute('SELECT COUNT(*) FROM episodes').fetchone()[0]
print(f"   ✓ Exportado: episodes.parquet ({episodes_count:,} registros)")

# ============================================================================
# RESUMEN Y ESTADÍSTICAS
# ============================================================================
elapsed_time = time.time() - start_time
print("\n" + "="*70)
print("✅ PIPELINE ETL COMPLETADO")
print("="*70)

# Calcular tamaños de archivos
import os
for file in OUTPUT_DIR.glob("*.parquet"):
    size_mb = os.path.getsize(file) / (1024 * 1024)
    print(f"📦 {file.name}: {size_mb:.2f} MB")

print(f"\n⏱️  Tiempo total: {elapsed_time:.2f} segundos")
print(f"📁 Archivos guardados en: {OUTPUT_DIR.absolute()}")

# Cerrar conexión
con.close()

print("\n🎉 Datos listos para subir a GitHub y usar en Streamlit!")