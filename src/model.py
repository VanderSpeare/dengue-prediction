import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import logging

def mean_squared_error(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean((y_true - y_pred) ** 2))

def mean_absolute_error(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))

try:
    from . import paths
except ImportError:
    import paths

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Base features (always used)
FEATURES_BASE = ['year', 'month', 'population', 'cases_lag_1', 'cases_lag_2',
                 'month_sin', 'month_cos', 'province']

# Weather features (used only when data contains these columns)
FEATURES_WEATHER = ['rain_lag_1', 'temp_lag_1', 'humidity_lag_1']

# Legacy alias — used by older code that references FEATURES directly
FEATURES = FEATURES_BASE


def _get_active_features(df: pd.DataFrame) -> list:
    """
    Tự động phát hiện feature set phù hợp với DataFrame.
    Nếu weather columns có mặt và không toàn 0 → dùng FEATURES_BASE + FEATURES_WEATHER.
    Ngược lại → chỉ dùng FEATURES_BASE (backward compatible).
    """
    has_weather = all(col in df.columns for col in FEATURES_WEATHER)
    if has_weather:
        # Kiểm tra weather cols không toàn 0 (tránh dùng khi chưa fetch)
        non_zero = sum((df[col] != 0).any() for col in FEATURES_WEATHER)
        if non_zero > 0:
            logger.info(f"Weather features detected ({non_zero}/{len(FEATURES_WEATHER)} non-zero). Using extended feature set.")
            return FEATURES_BASE + FEATURES_WEATHER
    return FEATURES_BASE


def prepare_features(historical_data, province_categories=None):
    """
    Adds temporal + lag features. Automatically includes weather lag features
    if they are present in the data (rain_lag_1, temp_lag_1, humidity_lag_1).

    province_categories: if provided, 'province' is cast to a category dtype
    with exactly these categories (so train-time and predict-time encodings
    always match, even if a given batch doesn't contain every province).
    """
    df = historical_data.copy()
    df = df.sort_values(by=['province', 'date'])

    # Create temporal features
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    # Create lag features (previous month's cases)
    df['cases_lag_1'] = df.groupby('province')['cases'].shift(1)
    df['cases_lag_2'] = df.groupby('province')['cases'].shift(2)
    df[['cases_lag_1', 'cases_lag_2']] = df[['cases_lag_1', 'cases_lag_2']].fillna(0)

    # Ensure weather cols exist (fill with 0 if not present — backward compat)
    for w_col in FEATURES_WEATHER:
        if w_col not in df.columns:
            df[w_col] = 0.0

    if province_categories is not None:
        df['province'] = pd.Categorical(df['province'], categories=province_categories)
    else:
        df['province'] = df['province'].astype('category')

    return df



def train_model(historical_data, model_path=None, test_months=3):
    """
    Trains an XGBoost regressor to predict monthly dengue cases per province.
    Automatically uses weather features (rain_lag_1, temp_lag_1, humidity_lag_1)
    if they are present and non-zero in historical_data.

    test_months: number of most-recent months held out as a time-based test set.
    """
    if model_path is None:
        model_path = paths.MODEL_FILE

    logger.info("Preparing features for model training...")
    province_categories = sorted(historical_data['province'].unique())
    data = prepare_features(historical_data, province_categories=province_categories)

    if len(data) < 10:
        logger.warning("Not enough data to train a meaningful model yet. Need at least 10 records.")
        return None

    # Auto-detect which features to use based on available data
    active_features = _get_active_features(data)
    logger.info(f"Active features ({len(active_features)}): {active_features}")

    unique_dates = sorted(data['date'].unique())
    if len(unique_dates) <= test_months:
        logger.warning(
            f"Only {len(unique_dates)} distinct months available; falling back to a random split "
            f"since a time-based holdout of {test_months} months isn't possible yet."
        )
        train_data = data.sample(frac=0.8, random_state=42)
        test_data = data.drop(train_data.index)
    else:
        cutoff_date = unique_dates[-test_months]
        train_data = data[data['date'] < cutoff_date]
        test_data = data[data['date'] >= cutoff_date]

    X_train, y_train = train_data[active_features], train_data['cases']
    X_test, y_test = test_data[active_features], test_data['cases']

    logger.info(f"Training XGBoost Booster on {len(X_train)} rows, testing on {len(X_test)} rows...")
    params = {
        'objective': 'reg:squarederror',
        'learning_rate': 0.05,
        'max_depth': 4,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'seed': 42
    }
    
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True) if len(X_test) > 0 else None

    model = xgb.train(params, dtrain, num_boost_round=200)

    metrics = {}
    if dtest is not None:
        preds = model.predict(dtest)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        metrics = {'rmse': rmse, 'mae': mae}
        logger.info(f"Model Evaluation (time-based holdout) - RMSE: {rmse:.2f}, MAE: {mae:.2f}")

    # Save model bundled with province categories, active features, and metrics
    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        'model': model,
        'province_categories': province_categories,
        'active_features': active_features,    # store which features were used
        'metrics': metrics
    }
    joblib.dump(bundle, model_path)
    logger.info(f"Model saved to {model_path}")

    return bundle



def predict_future(model_bundle, recent_history, n_months=3):
    """
    Predict future cases per province for the next `n_months` (default 3 months).

    IMPORTANT: `recent_history` must contain at least the last 3 months of
    data per province so that cases_lag_1/cases_lag_2 are computed from real history.

    If the model was trained with weather features, recent_history should
    include rain_lag_1, temp_lag_1, humidity_lag_1 columns.
    """
    model = model_bundle['model']
    province_categories = model_bundle['province_categories']
    # Use the feature set the model was actually trained with
    active_features = model_bundle.get('active_features', FEATURES_BASE)

    prepared = prepare_features(recent_history, province_categories=province_categories)

    # Keep only the latest month per province as baseline
    latest_idx = prepared.groupby('province', observed=True)['date'].idxmax()
    baseline = prepared.loc[latest_idx].copy()

    all_steps = []
    current_state = baseline.copy()

    for step in range(1, n_months + 1):
        pred_data = current_state.copy()
        pred_data['step'] = step

        # Roll forward one month
        next_month = current_state['month'] + 1
        next_year = current_state['year'].copy()
        # Handle wrap around
        wrapped = next_month > 12
        next_year[wrapped] = next_year[wrapped] + 1
        next_month[wrapped] = 1

        pred_data['month'] = next_month
        pred_data['year'] = next_year

        # Recompute sin/cos for the forecast month
        pred_data['month_sin'] = np.sin(2 * np.pi * pred_data['month'] / 12)
        pred_data['month_cos'] = np.cos(2 * np.pi * pred_data['month'] / 12)

        # Shift case lags:
        if step == 1:
            pred_data['cases_lag_2'] = baseline['cases_lag_1'].values
            pred_data['cases_lag_1'] = baseline['cases'].values
        else:
            pred_data['cases_lag_2'] = current_state['cases_lag_1'].values
            pred_data['cases_lag_1'] = current_state['predicted_cases'].values

        # Weather lags for forecast months
        for w_col in FEATURES_WEATHER:
            if w_col in baseline.columns:
                pred_data[w_col] = baseline[w_col].values

        # Generate predictions
        X_pred = pred_data[active_features]
        if hasattr(model, 'predict'):
            try:
                dpred = xgb.DMatrix(X_pred, enable_categorical=True)
                predictions = model.predict(dpred)
            except Exception:
                predictions = model.predict(X_pred)
        else:
            predictions = [0] * len(pred_data)

        pred_data['predicted_cases'] = np.clip(predictions, a_min=0, a_max=None)
        pred_data['month_label'] = pred_data.apply(lambda r: f"Tháng {int(r['month']):02d}/{int(r['year'])}", axis=1)

        all_steps.append(pred_data)
        current_state = pred_data.copy()

    result_df = pd.concat(all_steps, ignore_index=True)
    return result_df