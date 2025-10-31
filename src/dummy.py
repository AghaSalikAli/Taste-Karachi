import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import numpy as np
from sklearn.compose import ColumnTransformer

# ============================================
# STEP 1: Connect to your MLflow server
# ============================================
MLFLOW_TRACKING_URI = "http://54.196.196.185:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
print(f"MLflow Tracking URI: {mlflow.get_tracking_uri()}")

# ============================================
# STEP 2: Load your dataset
# ============================================
df = pd.read_csv("data/train_set.csv")

# --- Define Column Lists ---

# Categorical columns (object type)
CATEGORICAL_COLS = [
    'area',
    'price_level',
    'category'
]

# Numeric columns (float64 type)
NUMERIC_COLS = [
    'latitude',
    'longitude'
]

# Binary columns (bool type) - left as-is
BINARY_COLS = [
    'dine_in', 'takeout', 'delivery', 'reservable', 'serves_breakfast',
    'serves_lunch', 'serves_dinner', 'serves_coffee', 'serves_dessert',
    'outdoor_seating', 'live_music', 'good_for_children', 'good_for_groups',
    'good_for_watching_sports', 'restroom', 'parking_free_lot',
    'parking_free_street', 'accepts_debit_cards', 'accepts_cash_only',
    'wheelchair_accessible', 'is_open_24_7', 'open_after_midnight',
    'is_closed_any_day'
]

# All features
FEATURES = CATEGORICAL_COLS + NUMERIC_COLS + BINARY_COLS
TARGET = 'rating'

# --- Create Preprocessing Pipelines ---

# Categorical transformer: OneHotEncoder
categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Numeric transformer: StandardScaler
numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())
])

# --- Build the ColumnTransformer ---
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', categorical_transformer, CATEGORICAL_COLS),
        ('num', numeric_transformer, NUMERIC_COLS),
        ('bin', 'passthrough', BINARY_COLS)  # Leave binary columns unchanged
    ])

print("Preprocessing pipeline created successfully!")

# --- Prepare X and y ---
X = df[FEATURES]
y = df[TARGET]

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set size: {len(X_train)}")
print(f"Test set size: {len(X_test)}")

# ============================================
# STEP 3: Set experiment name
# ============================================
experiment_name = "test-experiment-2"
mlflow.set_experiment(experiment_name)

# ============================================
# STEP 4: Run experiment with MLflow tracking
# ============================================
with mlflow.start_run(run_name="random_forest_regression_test"):

    # Define hyperparameters
    n_estimators = 100
    max_depth = 10
    random_state = 42

    # Log parameters
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_param("random_state", random_state)
    mlflow.log_param("test_size", 0.2)

    # ============================================
    # Create FULL PIPELINE (Preprocessing + Model)
    # ============================================
    print("Creating full pipeline...")
    full_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        ))
    ])

    # Train the pipeline
    print("Training model...")
    full_pipeline.fit(X_train, y_train)

    # Make predictions
    y_pred = full_pipeline.predict(X_test)

    # Calculate regression metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    # Log metrics
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("mse", mse)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2_score", r2)

    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R² Score: {r2:.4f}")

    # ============================================
    # STEP 5: Log the FULL PIPELINE to MLflow
    # ============================================
    print("Logging model to MLflow...")
    mlflow.sklearn.log_model(
        full_pipeline,  # Log the entire pipeline (preprocessing + model)
        "random_forest_model",
        registered_model_name="test_model_regression"
    )

    print("✅ Model logged successfully!")
    print(f"Run ID: {mlflow.active_run().info.run_id}")

print("\n" + "="*50)
print("Experiment completed!")
print(f"View results at: {MLFLOW_TRACKING_URI}")
print("="*50)
