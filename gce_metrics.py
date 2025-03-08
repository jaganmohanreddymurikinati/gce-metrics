


from flask import Flask, request, jsonify
from google.cloud import monitoring_v3, compute_v1
from datetime import datetime, timedelta

app = Flask(__name__)

class GCEMetricsFetcher:
    def __init__(self, project_id, zone):
        self.project_id = project_id
        self.zone = zone
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.compute_client = compute_v1.InstancesClient()
        self.project_name = f"projects/{project_id}"

    def _fetch_metric(self, metric_type, duration=10):
        """Fetch time-series data for a given metric type."""
        filter_expression = f'metric.type="{metric_type}" AND resource.labels.zone="{self.zone}"'

        now = datetime.utcnow()
        interval = monitoring_v3.TimeInterval(
            start_time=(now - timedelta(minutes=duration)).isoformat() + "Z",
            end_time=now.isoformat() + "Z"
        )

        results = self.monitoring_client.list_time_series(
            name=self.project_name,
            filter=filter_expression,
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
        )

        metric_data = {}
        
        for result in results:
            instance_id = result.resource.labels["instance_id"]
            max_value = 0
            for point in result.points:
                if point.value.double_value != 0.0:
                    value = point.value.double_value
                    max_value = max(value, max_value)
                elif point.value.int64_value != 0:
                    value = point.value.int64_value
                    max_value = max(value, max_value)
            
            metric_data[instance_id] = max_value

        return metric_data

    def get_metrics(self):
        """Fetch and return multiple metrics as a dictionary."""
        return {
            "cpu_utilization": self._fetch_metric("compute.googleapis.com/instance/cpu/utilization", 10),
            "cpu_usage_time": self._fetch_metric("compute.googleapis.com/instance/cpu/usage_time", 10),
            "disk_read_ops": self._fetch_metric("compute.googleapis.com/instance/disk/read_ops_count", 10),
            "system_uptime": self._fetch_metric("compute.googleapis.com/instance/uptime_total", 10),
            "reserved_cores": self._fetch_metric("compute.googleapis.com/instance/cpu/reserved_cores", 10),
            "disk_io_latency": self._fetch_metric("compute.googleapis.com/instance/disk/average_io_latency", 20),
            "write_ops_count": self._fetch_metric("compute.googleapis.com/instance/disk/write_ops_count", 10),
            "sent_packets_count": self._fetch_metric("compute.googleapis.com/instance/network/sent_packets_count", 10),
            "received_packets_count": self._fetch_metric("compute.googleapis.com/instance/network/received_packets_count", 10),
            "nat_sent_packets_count": self._fetch_metric("compute.googleapis.com/nat/sent_packets_count", 10),
            "egress_packets_count": self._fetch_metric("networking.googleapis.com/vm_flow/egress_packets_count", 10),
            "ingress_packets_count": self._fetch_metric("networking.googleapis.com/vm_flow/ingress_packets_count", 10),
        }

@app.route("/")  # Defines the home page route
def home():
    return "Hello, Flask is working!"

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to fetch GCE instance metrics."""
    project_id = request.args.get('project_id')
    zone = request.args.get('zone')

    if not project_id or not zone:
        return jsonify({"error": "Missing project_id or zone"}), 400

    try:
        gcp_metrics = GCEMetricsFetcher(project_id, zone)
        metrics_data = gcp_metrics.get_metrics()
        return jsonify(metrics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

