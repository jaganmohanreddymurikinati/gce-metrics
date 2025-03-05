from google.cloud import monitoring_v3, compute_v1
from datetime import datetime, timedelta

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
            # latest_point = result.points[-2] if result.points else None
            # metric_value = latest_point.value.double_value if latest_point else 0
            # metric_data[instance_id] = metric_value

            max_value=0
            for point in result.points:
                # print(point.value)
                # print(type(point.value))
                # print(dir(point.value)) 
                if point.value.double_value != 0.0:
                    value = point.value.double_value
                    max_value=max(value,max_value)
                elif point.value.int64_value != 0:
                    value = point.value.int64_value
                    max_value=max(value,max_value)

            # max_value = max((point.value.int64_value for point in result.points), default=0)
            
            
            metric_data[instance_id] = max_value

        return metric_data

    def get_cpu_utilization(self):
        """Fetch CPU utilization (percentage) for all instances."""
        raw_data = self._fetch_metric("compute.googleapis.com/instance/cpu/utilization", 10)
        # print("cpu utilization",raw_data)
        return {key: value * 10 for key, value in raw_data.items()}  # Convert to percentage

    def get_cpu_usage_time(self):
        """Fetch CPU usage time for all instances."""
        return self._fetch_metric("compute.googleapis.com/instance/cpu/usage_time", 10)

    def get_disk_read_ops(self):
        """Fetch disk read operations for all instances."""
        return self._fetch_metric("compute.googleapis.com/instance/disk/read_ops_count", 10)

    def get_system_uptime(self):
        """Fetch system uptime for all instances."""
        return self._fetch_metric("compute.googleapis.com/instance/uptime_total", 10)
    def get_reserved_cpu_cores(self):
        """Fetch reserved cores for all instances."""
        return self._fetch_metric("compute.googleapis.com/instance/cpu/reserved_cores",10)

    def get_disk_average_io_latency(self):
        """Fetch disk average io latency."""
        return self._fetch_metric("compute.googleapis.com/instance/disk/average_io_latency",20)


    def get_read_ops_count(self):
        """Fetch Count of disk read IO operations"""
        return self._fetch_metric("compute.googleapis.com/instance/disk/read_ops_count",10)
    def get_write_ops_count(self):
        """Fetch Count of disk write IO operations"""
        return self._fetch_metric("compute.googleapis.com/instance/disk/write_ops_count",10)
    
    

    def get_sent_packets_count(self):
        return self._fetch_metric("compute.googleapis.com/instance/network/sent_packets_count",10)
    def get_write_bytes_count(self):
        return self._fetch_metric("compute.googleapis.com/instance/disk/write_bytes_count",10)
    
    def get_firewall_dropped_packets_count(self):
        return self._fetch_metric("compute.googleapis.com/firewall/dropped_packets_count",10)
    
    def get_ram_usage(self):
        """Fetch ram usage for all instances"""
        return self._fetch_metric("compute.googleapis.com/instance/memory/balloon/ram_used",10)
    
    def get_ram_size(self):
        """Fetch ram size for all instances"""
        return self._fetch_metric("compute.googleapis.com/instance/memory/balloon/ram_size",10)

    def get_instance_details(self):
        """Fetch instance details such as name and machine type."""
        instances = self.compute_client.list(project=self.project_id, zone=self.zone)
        return {instance.id: {"name": instance.name, "machine_type": instance.machine_type.split("/")[-1]} for instance in instances}

    def list_instances_with_metrics(self):
        """List all instances with their metrics."""
        cpu_utilization = self.get_cpu_utilization()
        cpu_usage_time = self.get_cpu_usage_time()
        disk_read_ops = self.get_disk_read_ops()
        instance_details = self.get_instance_details()
        system_uptime = self.get_system_uptime()
        reserved_cores=self.get_reserved_cpu_cores()
        disk_io_latency=self.get_disk_average_io_latency()
        disk_read_ops_count=self.get_read_ops_count()
        network_sent_packets_count=self.get_sent_packets_count()
        write_bytes_count=self.get_write_bytes_count()
        dropped_packets_count=self.get_firewall_dropped_packets_count()
        write_ops_count=self.get_write_ops_count()
        ram_used=self.get_ram_usage()
        ram_size=self.get_ram_size()
        

        # print("ram size: ",ram_used)
        # print("cpu utilization",cpu_utilization)

        print("ram_size: ",ram_size)
        print("ram_used : ",ram_used) #will give the output in bytes
        print("write ops count : ",write_ops_count)
        print("firewall dropped packets count : ",dropped_packets_count)
        print("Write bytes count : ",write_bytes_count)
        print("sent packets count : ",network_sent_packets_count)
        print("disk read ops : ",disk_read_ops_count)
        print("reserved-cores : ",reserved_cores)
        print("disk_average_io_latency : ",disk_io_latency)
        print("System uptime : ",system_uptime)
        print("CPU Utilization : ",cpu_utilization)
        print("CPU Usage time : ",cpu_usage_time)
        
        # print("\nInstance Metrics Report : ")
        # print("=" * 80)
        # print(f"{'Instance':<20} | {'Machine Type':<15} | {'CPU (%)':<10} | {'Read Ops':<10} | {'CPU Usage Time':<10} | {'Uptime (s)'}")
        # print("=" * 80)

        # for instance_id, details in instance_details.items():
        #     cpu_usage = round(cpu_utilization.get(str(instance_id), 0))
        #     read_ops = round(disk_read_ops.get(str(instance_id), 0))
        #     cpu_time = round(cpu_usage_time.get(str(instance_id), 0))
        #     uptime = round(system_uptime.get(str(instance_id), 0))
        #     reserved_vCpus=reserved_cores.get(str(instance_id),0)
        #     average_io_latency=disk_io_latency.get(str(instance_id),0)

        #     print(f"{details['name']:<20} | {details['machine_type']:<15} | {cpu_usage:<10} | {read_ops:<10} | {cpu_time:<10} | {uptime}")

if __name__ == "__main__":
    PROJECT_ID = "digital-splicer-448505-f3"
    ZONE = "us-central1-a"
    gcp_metrics = GCEMetricsFetcher(PROJECT_ID, ZONE)
    gcp_metrics.list_instances_with_metrics()
