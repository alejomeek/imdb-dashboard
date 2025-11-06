"""
Script de utilidad para verificar los datasets procesados
Muestra estadísticas y valida la integridad de los archivos Parquet
"""

import pandas as pd
from pathlib import Path
import sys

DATA_DIR = Path("data_processed")

def format_size(bytes):
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def verify_dataset(filepath):
    """Verifica un dataset y muestra estadísticas"""
    if not filepath.exists():
        print(f"❌ {filepath.name} - No encontrado")
        return False
    
    try:
        df = pd.read_parquet(filepath)
        size = filepath.stat().st_size
        
        print(f"\n{'='*70}")
        print(f"✅ {filepath.name}")
        print(f"{'='*70}")
        print(f"📦 Tamaño del archivo: {format_size(size)}")
        print(f"📊 Registros: {len(df):,}")
        print(f"📋 Columnas: {len(df.columns)}")
        print(f"\n🔍 Columnas: {', '.join(df.columns.tolist())}")
        
        # Verificar si hay valores nulos
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"\n⚠️  Columnas con valores nulos:")
            for col, count in null_counts[null_counts > 0].items():
                pct = (count / len(df)) * 100
                print(f"   - {col}: {count:,} ({pct:.2f}%)")
        else:
            print(f"\n✓ No hay valores nulos")
        
        # Mostrar primeras filas
        print(f"\n📄 Primeras 3 filas:")
        print(df.head(3).to_string())
        
        return True
        
    except Exception as e:
        print(f"❌ Error al leer {filepath.name}: {e}")
        return False

def main():
    """Verifica todos los datasets procesados"""
    
    print("🔍 Verificando datasets procesados de IMDb")
    print("="*70)
    
    if not DATA_DIR.exists():
        print(f"❌ Directorio {DATA_DIR} no existe")
        print("   Ejecuta primero el script etl_imdb.py")
        sys.exit(1)
    
    datasets = [
        'titles_clean.parquet',
        'genres_by_year.parquet',
        'directors.parquet',
        'actors.parquet',
        'countries.parquet',
        'episodes.parquet'
    ]
    
    results = {}
    total_size = 0
    
    for dataset in datasets:
        filepath = DATA_DIR / dataset
        results[dataset] = verify_dataset(filepath)
        if filepath.exists():
            total_size += filepath.stat().st_size
    
    # Resumen final
    print(f"\n{'='*70}")
    print("📊 RESUMEN")
    print(f"{'='*70}")
    
    success = sum(results.values())
    total = len(results)
    
    print(f"✅ Archivos válidos: {success}/{total}")
    print(f"📦 Tamaño total: {format_size(total_size)}")
    
    if success == total:
        print(f"\n🎉 Todos los datasets están listos para usar!")
        print(f"   Puedes ejecutar: streamlit run app.py")
    else:
        print(f"\n⚠️  Algunos datasets no están disponibles")
        print(f"   Ejecuta: python etl_imdb.py")
    
    # Verificar tamaño de GitHub
    if total_size > 100 * 1024 * 1024:  # 100 MB
        print(f"\n⚠️  ADVERTENCIA: Tamaño total > 100 MB")
        print(f"   Considera usar Git LFS o filtros más agresivos")

if __name__ == "__main__":
    main()