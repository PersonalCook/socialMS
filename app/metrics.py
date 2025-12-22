from prometheus_client import Counter, Histogram, Gauge

num_requests = Counter("http_requests_total", "Total number of HTTP requests", ["method", "endpoint", "status_code"])
num_errors = Counter("http_request_errors_total", "Total number of HTTP request errors", ["method", "endpoint", "status_code"])
request_latency = Histogram("http_request_latency_seconds", "HTTP request latency in seconds",  ["method", "endpoint"])
requests_in_progress = Gauge("http_requests_in_progress", "Number of HTTP requests in progress")
likes_total = Counter("likes_total", "Total number of likes", ["action","source", "status"])
comments_total = Counter("comments_total", "Total number of comments", ["source", "status"])
follows_total = Counter("follows_total", "Total number of follows", ["action","source", "status"])
saved_items_total = Counter("saved_items_total", "Total number of saved items", ["action","source", "status"])