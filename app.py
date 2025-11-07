"""
Dashboard Interactivo de IMDb - Análisis de Películas y Series
Proyecto académico de visualización de datos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="IMDb Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #F5C518;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #F5C518;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# CARGA DE DATOS CON CACHE
# ============================================================================

@st.cache_data
def load_data():
    """Carga todos los datasets procesados"""
    data_dir = Path("data_processed")
    
    # Verificar si estamos en local o en cloud
    if not data_dir.exists():
        # En Streamlit Cloud, usar ruta del repo
        data_dir = Path(".")
    
    return {
        'titles': pd.read_parquet(data_dir / "titles_clean.parquet"),
        'genres': pd.read_parquet(data_dir / "genres_by_year.parquet"),
        'directors': pd.read_parquet(data_dir / "directors.parquet"),
        'actors': pd.read_parquet(data_dir / "actors.parquet"),
        'countries': pd.read_parquet(data_dir / "countries.parquet"),
        'episodes': pd.read_parquet(data_dir / "episodes.parquet")
    }

# Cargar datos
with st.spinner("Cargando datos de IMDb..."):
    data = load_data()

# ============================================================================
# SIDEBAR - FILTROS GLOBALES
# ============================================================================

st.sidebar.markdown("# 🎬 Filtros")

# Filtro de años
year_range = st.sidebar.slider(
    "Rango de años",
    min_value=int(data['titles']['startYear'].min()),
    max_value=int(data['titles']['startYear'].max()),
    value=(1990, 2024)
)

# Filtro de tipo de contenido
content_types = st.sidebar.multiselect(
    "Tipo de contenido",
    options=['movie', 'tvSeries', 'tvMovie', 'tvMiniSeries', 'tvEpisode'],
    default=['movie', 'tvSeries']
)

# Filtro de rating mínimo
min_rating = st.sidebar.slider(
    "Rating mínimo",
    min_value=0.0,
    max_value=10.0,
    value=5.0,
    step=0.5,
    help="Filtra títulos, episodios y análisis relacionados con este rating mínimo"
)

st.sidebar.info("ℹ️ Los filtros se aplican a todos los análisis del dashboard")

# Aplicar filtros globales
df_filtered = data['titles'][
    (data['titles']['startYear'] >= year_range[0]) &
    (data['titles']['startYear'] <= year_range[1]) &
    (data['titles']['titleType'].isin(content_types)) &
    (data['titles']['averageRating'] >= min_rating)
]

# Obtener IDs de títulos filtrados para aplicar a otros datasets
filtered_ids = set(df_filtered['tconst'].unique())

# ============================================================================
# HEADER
# ============================================================================

st.markdown('<h1 class="main-header">📊 IMDb Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Análisis de la industria audiovisual (1950-2024)")
st.markdown("---")

# ============================================================================
# MÉTRICAS PRINCIPALES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📽️ Total de títulos",
        f"{len(df_filtered):,}",
        help="Títulos que cumplen los filtros"
    )

with col2:
    avg_rating = df_filtered['averageRating'].mean()
    st.metric(
        "⭐ Rating promedio",
        f"{avg_rating:.2f}",
        help="Rating promedio de IMDb"
    )

with col3:
    total_votes = df_filtered['numVotes'].sum()
    st.metric(
        "🗳️ Total de votos",
        f"{total_votes/1_000_000:.1f}M",
        help="Suma de todos los votos"
    )

with col4:
    top_year = df_filtered.groupby('startYear').size().idxmax()
    st.metric(
        "📅 Año más productivo",
        f"{top_year}",
        help="Año con más títulos"
    )

st.markdown("---")

# ============================================================================
# TABS PRINCIPALES
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Tendencias Temporales",
    "🎭 Géneros",
    "👥 Personas",
    "🌍 Geografía",
    "📺 Series"
])

# ============================================================================
# TAB 1: TENDENCIAS TEMPORALES
# ============================================================================

with tab1:
    st.header("Evolución temporal de la producción audiovisual")
    
    # Producción por año
    col1, col2 = st.columns([2, 1])
    
    with col1:
        productions_by_year = df_filtered.groupby(['startYear', 'titleType']).size().reset_index(name='count')
        
        fig_timeline = px.area(
            productions_by_year,
            x='startYear',
            y='count',
            color='titleType',
            title="Evolución de la producción por tipo de contenido",
            labels={'startYear': 'Año', 'count': 'Número de títulos', 'titleType': 'Tipo'},
            color_discrete_map={
                'movie': '#FF6B6B',
                'tvSeries': '#4ECDC4',
                'tvMovie': '#45B7D1',
                'tvMiniSeries': '#FFA07A',
                'tvEpisode': '#98D8C8'
            }
        )
        fig_timeline.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Insights")
        
        # Década con más producción
        df_filtered['decade'] = (df_filtered['startYear'] // 10) * 10
        top_decade = df_filtered.groupby('decade').size().idxmax()
        st.info(f"**Década más productiva:** {top_decade}s")
        
        # Crecimiento
        recent_5y = df_filtered[df_filtered['startYear'] >= year_range[1] - 5]
        old_5y = df_filtered[(df_filtered['startYear'] >= year_range[0]) & 
                            (df_filtered['startYear'] < year_range[0] + 5)]
        
        if len(old_5y) > 0:
            growth = ((len(recent_5y) - len(old_5y)) / len(old_5y)) * 100
            st.metric("Crecimiento", f"{growth:.1f}%", 
                     help="Comparando primeros 5 años vs últimos 5 años del rango")
    
    # Rating promedio por año
    st.markdown("### ⭐ Evolución del rating promedio")
    
    rating_by_year = df_filtered.groupby('startYear').agg({
        'averageRating': 'mean',
        'tconst': 'count'
    }).reset_index()
    rating_by_year.columns = ['startYear', 'avg_rating', 'count']
    
    fig_rating = go.Figure()
    fig_rating.add_trace(go.Scatter(
        x=rating_by_year['startYear'],
        y=rating_by_year['avg_rating'],
        mode='lines+markers',
        name='Rating promedio',
        line=dict(color='#F5C518', width=3),
        marker=dict(size=6)
    ))
    
    fig_rating.update_layout(
        height=350,
        xaxis_title="Año",
        yaxis_title="Rating promedio",
        yaxis_range=[0, 10],
        hovermode='x unified'
    )
    st.plotly_chart(fig_rating, use_container_width=True)

# ============================================================================
# TAB 2: GÉNEROS
# ============================================================================

with tab2:
    st.header("Análisis de géneros cinematográficos")
    
    # Filtrar datos de géneros con rating mínimo aplicado
    genres_filtered = data['genres'][
        (data['genres']['startYear'] >= year_range[0]) &
        (data['genres']['startYear'] <= year_range[1]) &
        (data['genres']['titleType'].isin(content_types)) &
        (data['genres']['avg_rating'] >= min_rating)  # Aplicar filtro de rating
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top géneros
        st.markdown("### 🏆 Géneros más populares")
        top_genres = genres_filtered.groupby('genre')['count'].sum().sort_values(ascending=False).head(10)
        
        if len(top_genres) > 0:
            fig_genres_bar = px.bar(
                x=top_genres.values,
                y=top_genres.index,
                orientation='h',
                title="Top 10 géneros por número de producciones",
                labels={'x': 'Número de títulos', 'y': 'Género'},
                color=top_genres.values,
                color_continuous_scale='Viridis'
            )
            fig_genres_bar.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_genres_bar, use_container_width=True)
        else:
            st.warning("⚠️ No hay géneros que cumplan los filtros seleccionados.")
    
    with col2:
        # Rating por género
        st.markdown("### ⭐ Rating promedio por género")
        genre_ratings = genres_filtered.groupby('genre').agg({
            'avg_rating': 'mean',
            'count': 'sum'
        }).sort_values('avg_rating', ascending=False).head(10)
        
        if len(genre_ratings) > 0:
            fig_genre_rating = px.bar(
                x=genre_ratings['avg_rating'],
                y=genre_ratings.index,
                orientation='h',
                title="Top 10 géneros mejor calificados",
                labels={'x': 'Rating promedio', 'y': 'Género'},
                color=genre_ratings['avg_rating'],
                color_continuous_scale='RdYlGn'
            )
            fig_genre_rating.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_genre_rating, use_container_width=True)
        else:
            st.warning("⚠️ No hay géneros que cumplan los filtros seleccionados.")
    
    # Evolución de géneros en el tiempo
    st.markdown("### 📈 Evolución de géneros populares en el tiempo")
    
    # Selector de géneros
    available_genres = genres_filtered['genre'].unique()
    selected_genres = st.multiselect(
        "Selecciona géneros para comparar:",
        options=sorted(available_genres),
        default=['Drama', 'Comedy', 'Action', 'Thriller'] if all(g in available_genres for g in ['Drama', 'Comedy', 'Action', 'Thriller']) else list(sorted(available_genres)[:4])
    )
    
    if selected_genres:
        genre_timeline = genres_filtered[genres_filtered['genre'].isin(selected_genres)]
        genre_timeline_agg = genre_timeline.groupby(['startYear', 'genre'])['count'].sum().reset_index()
        
        fig_genre_evolution = px.line(
            genre_timeline_agg,
            x='startYear',
            y='count',
            color='genre',
            title="Evolución temporal de géneros seleccionados",
            labels={'startYear': 'Año', 'count': 'Número de títulos', 'genre': 'Género'}
        )
        fig_genre_evolution.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_genre_evolution, use_container_width=True)

# ============================================================================
# TAB 3: PERSONAS (DIRECTORES Y ACTORES)
# ============================================================================

with tab3:
    st.header("Análisis de directores y actores")
    
    # Filtrar datos con rating mínimo aplicado
    directors_filtered = data['directors'][
        (data['directors']['startYear'] >= year_range[0]) &
        (data['directors']['startYear'] <= year_range[1]) &
        (data['directors']['titleType'].isin(content_types)) &
        (data['directors']['averageRating'] >= min_rating)  # Aplicar filtro de rating
    ]
    
    actors_filtered = data['actors'][
        (data['actors']['startYear'] >= year_range[0]) &
        (data['actors']['startYear'] <= year_range[1]) &
        (data['actors']['titleType'].isin(content_types)) &
        (data['actors']['averageRating'] >= min_rating)  # Aplicar filtro de rating
    ]
    
    # Selector: Directores o Actores
    person_type = st.radio("Selecciona:", ["👨‍🎬 Directores", "🎭 Actores"], horizontal=True)
    
    if person_type == "👨‍🎬 Directores":
        df_people = directors_filtered
        name_col = 'directorName'
        title = "Directores"
    else:
        df_people = actors_filtered
        name_col = 'actorName'
        title = "Actores"
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top por número de trabajos
        st.markdown(f"### 🏆 Top {title} más prolíficos")
        top_people_count = df_people.groupby(name_col).size().sort_values(ascending=False).head(15)
        
        if len(top_people_count) > 0:
            fig_top_count = px.bar(
                x=top_people_count.values,
                y=top_people_count.index,
                orientation='h',
                title=f"Top 15 {title.lower()} por número de trabajos",
                labels={'x': 'Número de títulos', 'y': 'Nombre'},
                color=top_people_count.values,
                color_continuous_scale='Blues'
            )
            fig_top_count.update_layout(height=500, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top_count, use_container_width=True)
        else:
            st.warning(f"⚠️ No hay {title.lower()} que cumplan los filtros seleccionados. Intenta reducir el rating mínimo.")
    
    with col2:
        # Top por rating promedio (con mínimo de trabajos)
        st.markdown(f"### ⭐ Top {title} mejor calificados")
        min_works = st.slider("Mínimo de trabajos:", 3, 20, 5)
        
        people_ratings = df_people.groupby(name_col).agg({
            'averageRating': 'mean',
            'tconst': 'count'
        }).reset_index()
        people_ratings.columns = [name_col, 'avg_rating', 'num_works']
        
        top_people_rating = people_ratings[people_ratings['num_works'] >= min_works].sort_values(
            'avg_rating', ascending=False
        ).head(15)
        
        if len(top_people_rating) > 0:
            fig_top_rating = px.bar(
                top_people_rating,
                x='avg_rating',
                y=name_col,
                orientation='h',
                title=f"Top 15 {title.lower()} por rating promedio (mín. {min_works} trabajos)",
                labels={'avg_rating': 'Rating promedio', name_col: 'Nombre'},
                color='avg_rating',
                color_continuous_scale='RdYlGn'
            )
            fig_top_rating.update_layout(height=500, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_top_rating, use_container_width=True)
        else:
            st.warning(f"⚠️ No hay {title.lower()} con al menos {min_works} trabajos que cumplan los filtros seleccionados. Intenta reducir el rating mínimo o el número de trabajos.")
    
    # Análisis por década
    st.markdown(f"### 📅 {title} por década")
    
    if len(df_people) > 0:
        df_people['decade'] = (df_people['startYear'] // 10) * 10
        people_by_decade = df_people.groupby(['decade', name_col]).size().reset_index(name='count')
        
        top_per_decade = people_by_decade.groupby('decade').apply(
            lambda x: x.nlargest(3, 'count')
        ).reset_index(drop=True)
        
        if len(top_per_decade) > 0:
            selected_decade = st.selectbox(
                "Selecciona una década:",
                options=sorted(top_per_decade['decade'].unique(), reverse=True)
            )
            
            decade_data = top_per_decade[top_per_decade['decade'] == selected_decade]
            
            if len(decade_data) > 0:
                fig_decade = px.bar(
                    decade_data,
                    x='count',
                    y=name_col,
                    orientation='h',
                    title=f"Top 3 {title.lower()} de la década de {int(selected_decade)}",
                    labels={'count': 'Número de trabajos', name_col: 'Nombre'},
                    color='count',
                    color_continuous_scale='Purples'
                )
                fig_decade.update_layout(height=300, showlegend=False, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_decade, use_container_width=True)
            else:
                st.warning(f"⚠️ No hay datos para la década de {int(selected_decade)}")
        else:
            st.warning(f"⚠️ No hay suficientes {title.lower()} para análisis por década.")
    else:
        st.warning(f"⚠️ No hay {title.lower()} que cumplan los filtros seleccionados.")

# ============================================================================
# TAB 4: GEOGRAFÍA
# ============================================================================

with tab4:
    st.header("Análisis geográfico de la producción")
    
    # Filtrar datos de países con rating mínimo aplicado
    countries_filtered = data['countries'][
        (data['countries']['startYear'] >= year_range[0]) &
        (data['countries']['startYear'] <= year_range[1]) &
        (data['countries']['titleType'].isin(content_types)) &
        (data['countries']['averageRating'] >= min_rating)  # Aplicar filtro de rating
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top países productores
        st.markdown("### 🌍 Top países productores")
        top_countries = countries_filtered.groupby('region').size().sort_values(ascending=False).head(20)
        
        if len(top_countries) > 0:
            fig_countries = px.bar(
                x=top_countries.values,
                y=top_countries.index,
                orientation='h',
                title="Top 20 países por número de producciones",
                labels={'x': 'Número de títulos', 'y': 'País (código ISO)'},
                color=top_countries.values,
                color_continuous_scale='Teal'
            )
            fig_countries.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_countries, use_container_width=True)
        else:
            st.warning("⚠️ No hay países que cumplan los filtros seleccionados.")
    
    with col2:
        # Rating promedio por país
        st.markdown("### ⭐ Rating promedio por país")
        min_productions = st.slider("Mínimo de producciones:", 10, 200, 50)
        
        country_ratings = countries_filtered.groupby('region').agg({
            'averageRating': 'mean',
            'tconst': 'count'
        }).reset_index()
        country_ratings.columns = ['region', 'avg_rating', 'count']
        
        top_country_ratings = country_ratings[country_ratings['count'] >= min_productions].sort_values(
            'avg_rating', ascending=False
        ).head(20)
        
        if len(top_country_ratings) > 0:
            fig_country_ratings = px.bar(
                top_country_ratings,
                x='avg_rating',
                y='region',
                orientation='h',
                title=f"Top 20 países por rating (mín. {min_productions} producciones)",
                labels={'avg_rating': 'Rating promedio', 'region': 'País (código ISO)'},
                color='avg_rating',
                color_continuous_scale='RdYlGn'
            )
            fig_country_ratings.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_country_ratings, use_container_width=True)
        else:
            st.warning(f"⚠️ No hay países con al menos {min_productions} producciones que cumplan los filtros.")
    
    # Evolución temporal por país
    st.markdown("### 📈 Evolución de producción por país")
    
    available_countries = countries_filtered['region'].unique()
    selected_countries = st.multiselect(
        "Selecciona países para comparar (código ISO):",
        options=sorted(available_countries),
        default=['US', 'GB', 'FR', 'ES'] if all(c in available_countries for c in ['US', 'GB', 'FR', 'ES']) else list(sorted(available_countries)[:4])
    )
    
    if selected_countries:
        country_timeline = countries_filtered[countries_filtered['region'].isin(selected_countries)]
        country_timeline_agg = country_timeline.groupby(['startYear', 'region']).size().reset_index(name='count')
        
        fig_country_evolution = px.line(
            country_timeline_agg,
            x='startYear',
            y='count',
            color='region',
            title="Evolución temporal de producción por país",
            labels={'startYear': 'Año', 'count': 'Número de títulos', 'region': 'País'}
        )
        fig_country_evolution.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_country_evolution, use_container_width=True)

# ============================================================================
# TAB 5: SERIES Y EPISODIOS
# ============================================================================

with tab5:
    st.header("Análisis de series y estructura de episodios")
    
    # Filtrar solo series con rating mínimo
    series_filtered = df_filtered[df_filtered['titleType'].isin(['tvSeries', 'tvMiniSeries'])]
    
    # Filtrar episodios - usar rating de la serie o del episodio
    episodes_filtered = data['episodes'][
        (data['episodes']['seriesStartYear'] >= year_range[0]) &
        (data['episodes']['seriesStartYear'] <= year_range[1]) &
        (data['episodes']['episodeRating'] >= min_rating)  # Aplicar filtro de rating a episodios
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📺 Total de series", f"{len(series_filtered):,}")
        st.metric("📋 Total de episodios", f"{len(episodes_filtered):,}")
    
    with col2:
        avg_episodes = episodes_filtered.groupby('seriesId').size().mean()
        st.metric("📊 Promedio de episodios por serie", f"{avg_episodes:.1f}")
    
    # Top series por rating
    st.markdown("### 🏆 Top series mejor calificadas")
    
    if len(series_filtered) > 0:
        top_series = series_filtered.nlargest(20, 'averageRating')[
            ['primaryTitle', 'startYear', 'averageRating', 'numVotes']
        ]
        
        fig_top_series = px.bar(
            top_series,
            x='averageRating',
            y='primaryTitle',
            orientation='h',
            title="Top 20 series por rating",
            labels={'averageRating': 'Rating', 'primaryTitle': 'Serie'},
            color='averageRating',
            color_continuous_scale='Viridis',
            hover_data=['startYear', 'numVotes']
        )
        fig_top_series.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_top_series, use_container_width=True)
    else:
        st.warning("⚠️ No hay series que cumplan los filtros seleccionados.")
    
    # Análisis de temporadas
    st.markdown("### 📊 Análisis de temporadas")
    
    seasons_analysis = episodes_filtered.groupby('seriesId').agg({
        'seasonNumber': 'max',
        'episodeId': 'count',
        'episodeRating': 'mean'
    }).reset_index()
    seasons_analysis.columns = ['seriesId', 'num_seasons', 'num_episodes', 'avg_rating']
    
    # Merge con títulos
    seasons_analysis = seasons_analysis.merge(
        series_filtered[['tconst', 'primaryTitle']],
        left_on='seriesId',
        right_on='tconst'
    )
    
    col1, col2 = st.columns(2)
    
    if len(seasons_analysis) > 0:
        with col1:
            # Series con más temporadas
            top_seasons = seasons_analysis.nlargest(15, 'num_seasons')
            
            if len(top_seasons) > 0:
                fig_seasons = px.bar(
                    top_seasons,
                    x='num_seasons',
                    y='primaryTitle',
                    orientation='h',
                    title="Series con más temporadas",
                    labels={'num_seasons': 'Número de temporadas', 'primaryTitle': 'Serie'},
                    color='num_seasons',
                    color_continuous_scale='Blues'
                )
                fig_seasons.update_layout(height=500, showlegend=False, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_seasons, use_container_width=True)
            else:
                st.warning("⚠️ No hay suficientes datos para mostrar series por temporadas.")
        
        with col2:
            # Series con más episodios
            top_episodes = seasons_analysis.nlargest(15, 'num_episodes')
            
            if len(top_episodes) > 0:
                fig_episodes = px.bar(
                    top_episodes,
                    x='num_episodes',
                    y='primaryTitle',
                    orientation='h',
                    title="Series con más episodios",
                    labels={'num_episodes': 'Número de episodios', 'primaryTitle': 'Serie'},
                    color='num_episodes',
                    color_continuous_scale='Greens'
                )
                fig_episodes.update_layout(height=500, showlegend=False, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_episodes, use_container_width=True)
            else:
                st.warning("⚠️ No hay suficientes datos para mostrar series por episodios.")
    else:
        st.warning("⚠️ No hay series con episodios que cumplan los filtros seleccionados.")
    
    # Evolución de rating por temporada
    st.markdown("### 📈 Evolución de rating por temporada")
    
    # Selector de serie
    series_list = seasons_analysis.nlargest(100, 'num_seasons')['primaryTitle'].tolist()
    selected_series = st.selectbox(
        "Selecciona una serie:",
        options=series_list
    )
    
    if selected_series:
        series_id = seasons_analysis[seasons_analysis['primaryTitle'] == selected_series]['seriesId'].iloc[0]
        series_episodes = episodes_filtered[episodes_filtered['seriesId'] == series_id]
        
        season_ratings = series_episodes.groupby('seasonNumber')['episodeRating'].mean().reset_index()
        
        fig_season_evolution = px.line(
            season_ratings,
            x='seasonNumber',
            y='episodeRating',
            markers=True,
            title=f"Evolución del rating promedio por temporada - {selected_series}",
            labels={'seasonNumber': 'Temporada', 'episodeRating': 'Rating promedio'}
        )
        fig_season_evolution.update_layout(height=350)
        fig_season_evolution.update_traces(line=dict(color='#F5C518', width=3), marker=dict(size=10))
        st.plotly_chart(fig_season_evolution, use_container_width=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>📊 Dashboard desarrollado con Streamlit | 🎬 Datos de IMDb</p>
    <p>Proyecto académico de visualización de datos</p>
</div>
""", unsafe_allow_html=True)
