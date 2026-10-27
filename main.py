import sys
import pandas as pd

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from src import paths
from src.data_processor import load_and_process_new_data
from src.model import train_model, predict_future
from src.gis_mapper import create_map_data

# Number of trailing months of history to feed predict_future so it can
# compute real lag_1/lag_2 features instead of falling back to 0.
LAG_MONTHS_NEEDED = 3


def main():
    print("🚀 Starting Dengue Outbreak Processing Pipeline...")

    if not paths.RAW_DATA_FILE.exists():
        print(f"❌ Raw file {paths.RAW_DATA_FILE} not found. Please place the patient data there.")
        return

    print("\n--- 1. Processing Data ---")
    new_data = load_and_process_new_data(paths.RAW_DATA_FILE, paths.POP_DATA_FILE)

    if new_data.empty:
        print("❌ No data processed.")
        return

    print(f"✅ Processed {len(new_data)} aggregated records.")

    # Save to processed folder
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    new_data.to_csv(paths.HISTORICAL_CSV, index=False)

    # 2. Train Model and Predict
    print("\n--- 2. Training Predictive Model ---")
    model_bundle = train_model(new_data)

    map_df = new_data
    if model_bundle:
        print("\n--- 3. Generating Predictions ---")

        # Use the last few months of data per province, not just the single
        # latest month, so the model can compute real lag features instead
        # of treating missing history as 0.
        unique_dates = sorted(new_data['date'].unique())
        cutoff_dates = unique_dates[-LAG_MONTHS_NEEDED:]
        recent_history = new_data[new_data['date'].isin(cutoff_dates)]

        predictions = predict_future(model_bundle, recent_history)

        latest_date = new_data['date'].max()
        latest_data_subset = new_data[new_data['date'] == latest_date]

        # Merge predictions back for mapping
        map_df = pd.merge(
            latest_data_subset,
            predictions[['province', 'predicted_cases']],
            on='province',
            how='left'
        )

        # Persist predictions so the dashboard can show the forecast too -
        # previously predicted_cases only ever reached the GeoJSON export
        # and was never saved anywhere the dashboard could read it.
        predictions_out = predictions[['province', 'year', 'month', 'predicted_cases']].copy()
        predictions_path = paths.PROCESSED_DIR / 'latest_predictions.csv'
        predictions_out.to_csv(predictions_path, index=False)
        print(f"✅ Predictions saved to {predictions_path}")
    else:
        print("⚠️  Skipping predictions - not enough historical data to train a model yet.")

    # 4. GIS Mapping
    print("\n--- 4. Creating GIS GeoJSON ---")
    create_map_data(map_df)

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