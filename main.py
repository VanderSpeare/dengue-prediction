import sys
import pandas as pd

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from src import paths
from src.data_processor import load_and_process_new_data
from src.model import (
    train_model,
    predict_future,
    train_district_model,
    predict_future_districts,
)
from src.gis_mapper import (
    create_map_data,
    create_cluster_geojson,
    ensure_hcmc_districts_geojson,
    create_hcmc_district_map_data,
)

# Number of trailing months of history to feed predict_future so it can
# compute real lag_1/lag_2 features instead of falling back to 0.
LAG_MONTHS_NEEDED = 3


def main():
    print("🚀 Starting Dengue Outbreak Processing Pipeline...")

    raw_source = paths.RAW_DATA_DIR if paths.RAW_DATA_DIR.exists() and any(paths.RAW_DATA_DIR.glob("*.xlsx")) else paths.RAW_DATA_FILE
    if not raw_source.exists():
        print(f"❌ Raw data {raw_source} not found. Please place the patient data there.")
        return

    print(f"\n--- 1. Processing Data from {raw_source} ---")
    new_data = load_and_process_new_data(raw_source, paths.POP_DATA_FILE)

    if new_data.empty:
        print("❌ No data processed.")
        return

    print(f"✅ Processed {len(new_data)} aggregated records.")

    # Save to processed folder
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    new_data.to_csv(paths.HISTORICAL_CSV, index=False)

    # 2. Train Model and Predict (Province Level - 34 Provinces)
    print("\n--- 2. Training Predictive Model (Province Level) ---")
    model_bundle = train_model(new_data)

    map_df = new_data
    if model_bundle:
        print("\n--- 3. Generating Province Predictions ---")

        unique_dates = sorted(new_data['date'].unique())
        cutoff_dates = unique_dates[-LAG_MONTHS_NEEDED:]
        recent_history = new_data[new_data['date'].isin(cutoff_dates)]

        predictions = predict_future(model_bundle, recent_history)

        latest_date = new_data['date'].max()
        latest_data_subset = new_data[new_data['date'] == latest_date]

        step1_preds = predictions[predictions['step'] == 1] if 'step' in predictions.columns else predictions
        map_df = pd.merge(
            latest_data_subset,
            step1_preds[['province', 'predicted_cases']],
            on='province',
            how='left'
        )

        out_cols = [c for c in ['province', 'year', 'month', 'step', 'month_label', 'predicted_cases'] if c in predictions.columns]
        predictions_out = predictions[out_cols].copy()
        predictions_path = paths.PREDICTIONS_CSV
        predictions_out.to_csv(predictions_path, index=False)
        print(f"✅ Province predictions saved to {predictions_path}")
    else:
        print("⚠️  Skipping province predictions - not enough historical data to train a model yet.")

    # 3.5. HCMC District-Level XGBoost Model & Predictions
    print("\n--- 3.5. Training & Predicting HCMC District Model ---")
    dist_df = pd.DataFrame()
    dist_predictions = pd.DataFrame()
    if paths.DISTRICT_CSV.exists():
        dist_df = pd.read_csv(paths.DISTRICT_CSV)
        weather_df = pd.read_csv(paths.WEATHERDATA_MONTHLY_CSV) if paths.WEATHERDATA_MONTHLY_CSV.exists() else None
        dist_bundle = train_district_model(dist_df, weather_df=weather_df)
        if dist_bundle:
            dist_predictions = predict_future_districts(dist_bundle, dist_df, weather_df=weather_df, n_months=3)
            if not dist_predictions.empty:
                dist_predictions.to_csv(paths.DISTRICT_PREDICTIONS_CSV, index=False)
                print(f"✅ HCMC district predictions saved to {paths.DISTRICT_PREDICTIONS_CSV} ({len(dist_predictions)} rows)")
        else:
            print("⚠️  Skipping HCMC district predictions - insufficient district data.")
    else:
        print(f"⚠️  District file {paths.DISTRICT_CSV} not found; skipping HCMC district model.")

    # 4. GIS Mapping (Province + HCMC Districts + Epidemic Clusters)
    print("\n--- 4. Creating GIS GeoJSON Layers ---")
    create_map_data(map_df)
    ensure_hcmc_districts_geojson()
    if not dist_df.empty:
        create_hcmc_district_map_data(dist_df, predictions_df=dist_predictions)
    if paths.EPIDEMIC_CLUSTERS_CSV.exists():
        clusters_df = pd.read_csv(paths.EPIDEMIC_CLUSTERS_CSV)
        create_cluster_geojson(clusters_df)

    # 5. Ingest Chatbot Knowledge Base
    print("\n--- 5. Ingesting Chatbot Knowledge Base ---")
    try:
        from src.chatbot.ingest import build_vector_store
        build_vector_store()
    except Exception as e:
        print(f"⚠️ Vector store build note: {e}")

    print("\n🎉 Pipeline Complete! To run the dashboard, use:")
    print("streamlit run src/dashboard.py")



if __name__ == "__main__":
    main()