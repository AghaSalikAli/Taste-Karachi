import warnings

import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

warnings.filterwarnings("ignore")

# Load datasets
train_data = pd.read_csv("data/train_set.csv")
test_data = pd.read_csv("data/holdout_test_set.csv")

# Convert Index objects to lists
numeric_features = train_data.select_dtypes(
    include=["int64", "float64"]
).columns.tolist()
categorical_features = train_data.select_dtypes(include=["object"]).columns.tolist()

column_mapping = ColumnMapping(
    numerical_features=numeric_features, categorical_features=categorical_features
)

# Create Data Drift report
data_drift_report = Report(
    metrics=[
        DataDriftPreset(),
    ]
)

data_drift_report.run(
    reference_data=train_data, current_data=test_data, column_mapping=column_mapping
)

# Save the report
data_drift_report.save_html("data_drift_report.html")

# Start local server
import http.server
import socketserver

PORT = 4000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    print(
        "Open your browser and navigate to http://localhost:4000/data_drift_report.html"
    )
    httpd.serve_forever()
