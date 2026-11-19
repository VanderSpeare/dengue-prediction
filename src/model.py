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
FEATURES_WEATHER_EXTENDED = [
    'rain_lag_1', 'rain_lag_2',
    'temp_lag_1', 'temp_lag_2',
    'humidity_lag_1', 'humidity_lag_2',
    'temp_humidity_interaction', 'pm25_lag_1'
]

# Legacy alias — used by older code that references FEATURES directly
FEATURES = FEATURES_BASE


def _get_active_features(df: pd.DataFrame) -> list:
    """
    Tự động phát hiện feature set phù hợp với DataFrame.
    Nếu weather columns mở rộng có mặt và không toàn 0 → dùng FEATURES_BASE + các cột weather có dữ liệu.
    Ngược lại nếu weather cơ bản có mặt → dùng FEATURES_BASE + FEATURES_WEATHER.
    Ngược lại → chỉ dùng FEATURES_BASE (backward compatible).
    """
    ext_present = [col for col in FEATURES_WEATHER_EXTENDED if col in df.columns and (df[col] != 0).any()]
    if len(ext_present) > len(FEATURES_WEATHER):
        logger.info(f"Extended weather features detected ({len(ext_present)}): {ext_present}")
        return FEATURES_BASE + ext_present

    has_weather = all(col in df.columns for col in FEATURES_WEATHER)
    if has_weather:
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


# ===========================================================================
# HCMC DISTRICT-LEVEL XGBOOST MODEL (Cấp Quận / Huyện TP. Hồ Chí Minh)
# ===========================================================================

FEATURES_DISTRICT_BASE = [
    'year', 'month', 'cases_lag_1', 'cases_lag_2',
    'month_sin', 'month_cos', 'district'
]


def _normalize_district_name(name: str) -> str:
    s = str(name or "").strip()
    if s == "Thành Phố Thủ Đức":
        return "Thủ Đức"
    return s


def prepare_district_features(
    district_data: pd.DataFrame,
    weather_df: pd.DataFrame = None,
    district_categories: list = None,
    province: str = "TP. Hồ Chí Minh"
) -> pd.DataFrame:
    """
    Chuẩn hóa dữ liệu ca bệnh cấp Quận/Huyện thành chuỗi thời gian liên tục (dense monthly panel),
    tạo đặc trưng chu kỳ sin/cos, độ trễ ca bệnh (cases_lag_1, cases_lag_2) và ghép dữ liệu
    khí tượng (rain_lag_1/2, temp_lag_1/2, humidity_lag_1/2, temp_humidity_interaction, pm25_lag_1).
    """
    df = district_data.copy()
    if 'province' in df.columns and province:
        df = df[df['province'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)].copy()

    if df.empty or 'district' not in df.columns:
        return pd.DataFrame()

    df['district'] = df['district'].apply(_normalize_district_name)
    df = df[~df['district'].isin(['', 'Chưa xác định', 'nan', 'None'])].copy()
    if df.empty:
        return pd.DataFrame()

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        df['date'] = pd.to_datetime(
            df['year'].astype(int).astype(str) + '-' + df['month'].astype(int).astype(str).str.zfill(2) + '-01'
        ) + pd.offsets.MonthEnd(0)

    df['year'] = df['date'].dt.year.astype(int)
    df['month'] = df['date'].dt.month.astype(int)

    # Gom tổng ca theo (district, year, month)
    grouped = (
        df.groupby(['district', 'year', 'month'], as_index=False)['cases']
        .sum()
    )
    grouped['ym_period'] = pd.PeriodIndex.from_fields(year=grouped['year'], month=grouped['month'], freq='M')

    min_p = grouped['ym_period'].min()
    max_p = grouped['ym_period'].max()
    all_periods = pd.period_range(min_p, max_p, freq='M')
    districts = district_categories if district_categories is not None else sorted(grouped['district'].unique())

    panel_idx = pd.MultiIndex.from_product([districts, all_periods], names=['district', 'ym_period'])
    panel = pd.DataFrame(index=panel_idx).reset_index()
    panel['year'] = panel['ym_period'].dt.year.astype(int)
    panel['month'] = panel['ym_period'].dt.month.astype(int)
    panel['date'] = panel['ym_period'].dt.to_timestamp('M')

    panel = panel.merge(
        grouped[['district', 'year', 'month', 'cases']],
        on=['district', 'year', 'month'],
        how='left'
    )
    panel['cases'] = panel['cases'].fillna(0.0)
    panel['province'] = province

    panel = panel.sort_values(['district', 'date']).reset_index(drop=True)
    panel['month_sin'] = np.sin(2 * np.pi * panel['month'] / 12.0)
    panel['month_cos'] = np.cos(2 * np.pi * panel['month'] / 12.0)
    panel['cases_lag_1'] = panel.groupby('district')['cases'].shift(1).fillna(0.0)
    panel['cases_lag_2'] = panel.groupby('district')['cases'].shift(2).fillna(0.0)

    # Ghép đặc trưng khí hậu TP.HCM theo tháng nếu có
    if weather_df is not None and not weather_df.empty:
        w = weather_df.copy()
        if 'province' in w.columns:
            w_hcm = w[w['province'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)]
            if not w_hcm.empty:
                w = w_hcm
        w = w.sort_values(['year', 'month']).drop_duplicates(subset=['year', 'month'], keep='last').copy()

        # Tính độ trễ khí hậu trước khi merge vào panel
        if 'precipitation_sum' in w.columns:
            w['rain_lag_1'] = w['precipitation_sum'].shift(1).fillna(w['precipitation_sum'])
            w['rain_lag_2'] = w['precipitation_sum'].shift(2).fillna(w['rain_lag_1'])
        if 'temp_mean' in w.columns:
            w['temp_lag_1'] = w['temp_mean'].shift(1).fillna(w['temp_mean'])
            w['temp_lag_2'] = w['temp_mean'].shift(2).fillna(w['temp_lag_1'])
        if 'humidity_mean' in w.columns:
            w['humidity_lag_1'] = w['humidity_mean'].shift(1).fillna(w['humidity_mean'])
            w['humidity_lag_2'] = w['humidity_mean'].shift(2).fillna(w['humidity_lag_1'])
        if 'pm25_mean' in w.columns:
            w['pm25_lag_1'] = w['pm25_mean'].shift(1).fillna(w['pm25_mean'].median() if w['pm25_mean'].notna().any() else 0.0)
            w['pm25_lag_1'] = w['pm25_lag_1'].fillna(0.0)
        if 'temp_lag_1' in w.columns and 'humidity_lag_1' in w.columns:
            w['temp_humidity_interaction'] = (w['temp_lag_1'] * w['humidity_lag_1']) / 100.0

        w_cols = ['year', 'month'] + [c for c in FEATURES_WEATHER_EXTENDED if c in w.columns]
        panel = panel.merge(w[w_cols], on=['year', 'month'], how='left')

    for w_col in FEATURES_WEATHER_EXTENDED:
        if w_col not in panel.columns:
            panel[w_col] = 0.0
        else:
            panel[w_col] = panel[w_col].fillna(panel[w_col].median() if panel[w_col].notna().any() else 0.0)

    panel['district'] = pd.Categorical(panel['district'], categories=districts)
    return panel


def train_district_model(
    district_data: pd.DataFrame,
    weather_df: pd.DataFrame = None,
    model_path=None,
    province: str = "TP. Hồ Chí Minh",
    test_months: int = 3
):
    """
    Huấn luyện mô hình XGBoost Regressor dự báo số ca Sốt xuất huyết hàng tháng
    cho từng Quận/Huyện tại TP. Hồ Chí Minh.
    """
    if model_path is None:
        model_path = getattr(paths, 'DISTRICT_MODEL_FILE', paths.MODELS_DIR / "dengue_xgboost_hcmc_districts.pkl")

    raw_hcm = district_data.copy()
    if 'province' in raw_hcm.columns:
        raw_hcm = raw_hcm[raw_hcm['province'].astype(str).str.contains('Hồ Chí Minh', case=False, na=False)]
    if raw_hcm.empty:
        logger.warning("Không có dữ liệu cấp Quận/Huyện cho TP. Hồ Chí Minh.")
        return None

    district_categories = sorted(
        {
            _normalize_district_name(d)
            for d in raw_hcm['district'].dropna().unique()
            if _normalize_district_name(d) not in ('', 'Chưa xác định', 'nan', 'None')
        }
    )

    data = prepare_district_features(
        raw_hcm,
        weather_df=weather_df,
        district_categories=district_categories,
        province=province,
    )
    if len(data) < 12:
        logger.warning("Chưa đủ bản ghi cấp Quận/Huyện để huấn luyện XGBoost.")
        return None

    weather_active = [c for c in FEATURES_WEATHER_EXTENDED if c in data.columns and (data[c] != 0).any()]
    active_features = FEATURES_DISTRICT_BASE + weather_active
    logger.info(f"District XGBoost active features ({len(active_features)}): {active_features}")

    unique_dates = sorted(data['date'].unique())
    if len(unique_dates) <= test_months:
        train_data = data.sample(frac=0.8, random_state=42)
        test_data = data.drop(train_data.index)
    else:
        cutoff_date = unique_dates[-test_months]
        train_data = data[data['date'] < cutoff_date]
        test_data = data[data['date'] >= cutoff_date]

    X_train, y_train = train_data[active_features], train_data['cases']
    X_test, y_test = test_data[active_features], test_data['cases']

    params = {
        'objective': 'reg:squarederror',
        'learning_rate': 0.05,
        'max_depth': 4,
        'subsample': 0.85,
        'colsample_bytree': 0.85,
        'seed': 42
    }

    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dtest = xgb.DMatrix(X_test, label=y_test, enable_categorical=True) if len(X_test) > 0 else None
    model = xgb.train(params, dtrain, num_boost_round=220)

    metrics = {}
    if dtest is not None:
        preds = np.clip(model.predict(dtest), a_min=0, a_max=None)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        metrics = {'rmse': rmse, 'mae': mae}
        logger.info(f"HCMC District Model Evaluation - RMSE: {rmse:.2f}, MAE: {mae:.2f}")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        'model': model,
        'district_categories': district_categories,
        'active_features': active_features,
        'metrics': metrics,
        'province': province
    }
    joblib.dump(bundle, model_path)
    logger.info(f"✅ HCMC District XGBoost model saved to {model_path}")
    return bundle


def predict_future_districts(
    model_bundle: dict,
    recent_district_history: pd.DataFrame,
    weather_df: pd.DataFrame = None,
    n_months: int = 3
) -> pd.DataFrame:
    """
    Dự báo đệ quy số ca Sốt xuất huyết n_months kế tiếp cho từng Quận/Huyện tại TP. Hồ Chí Minh.
    """
    if not model_bundle:
        return pd.DataFrame()

    model = model_bundle['model']
    district_categories = model_bundle['district_categories']
    active_features = model_bundle.get('active_features', FEATURES_DISTRICT_BASE)
    province = model_bundle.get('province', 'TP. Hồ Chí Minh')

    prepared = prepare_district_features(
        recent_district_history,
        weather_df=weather_df,
        district_categories=district_categories,
        province=province,
    )
    if prepared.empty:
        return pd.DataFrame()

    latest_date = prepared['date'].max()
    baseline = prepared[prepared['date'] == latest_date].copy()
    if baseline.empty:
        return pd.DataFrame()

    all_steps = []
    current_state = baseline.copy()

    for step in range(1, n_months + 1):
        pred_data = current_state.copy()
        pred_data['step'] = step

        next_month = current_state['month'] + 1
        next_year = current_state['year'].copy()
        wrapped = next_month > 12
        next_year[wrapped] = next_year[wrapped] + 1
        next_month[wrapped] = 1

        pred_data['month'] = next_month
        pred_data['year'] = next_year
        pred_data['month_sin'] = np.sin(2 * np.pi * pred_data['month'] / 12.0)
        pred_data['month_cos'] = np.cos(2 * np.pi * pred_data['month'] / 12.0)

        if step == 1:
            pred_data['cases_lag_2'] = baseline['cases_lag_1'].values
            pred_data['cases_lag_1'] = baseline['cases'].values
        else:
            pred_data['cases_lag_2'] = current_state['cases_lag_1'].values
            pred_data['cases_lag_1'] = current_state['predicted_cases'].values

        # Nếu có dữ liệu khí tượng tương ứng tháng dự báo trong weather_df thì cập nhật, ngược lại giữ baseline
        for w_col in FEATURES_WEATHER_EXTENDED:
            if w_col in baseline.columns:
                pred_data[w_col] = baseline[w_col].values

        X_pred = pred_data[active_features]
        dpred = xgb.DMatrix(X_pred, enable_categorical=True)
        preds = model.predict(dpred)
        pred_data['predicted_cases'] = np.clip(preds, a_min=0, a_max=None)
        pred_data['month_label'] = pred_data.apply(
            lambda r: f"Tháng {int(r['month']):02d}/{int(r['year'])}", axis=1
        )
        pred_data['province'] = province

        all_steps.append(pred_data)
        current_state = pred_data.copy()

    result_df = pd.concat(all_steps, ignore_index=True)
    return result_df[['province', 'district', 'year', 'month', 'step', 'predicted_cases', 'month_label']]