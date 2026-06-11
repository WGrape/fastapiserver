"""
Gunicorn 配置文件（统一所有环境）
使用 gunicorn 管理进程，uvicorn 作为 worker 处理异步请求
"""
import multiprocessing
import os

# 绑定地址 - 服务监听的IP和端口
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8000')}"

# Worker 数量 - 同时处理请求的进程数，推荐公式：CPU核心数 * 2 + 1
max_workers = multiprocessing.cpu_count() * 2 + 1
workers = int(os.getenv('WORKERS', min(max_workers, 4)))  # 默认最多4个，可通过环境变量调整

# Worker 类型 - 使用 Uvicorn Worker 处理异步请求，支持 async/await
worker_class = "uvicorn.workers.UvicornWorker"

# 每个 Worker 的最大连接数 - 单个进程同时处理的连接数，异步 worker 可以设大一些
worker_connections = int(os.getenv('WORKER_CONNECTIONS', '1000'))

# 请求超时时间 - 处理一个请求的最大秒数，超时后 worker 会被重启
timeout = int(os.getenv('TIMEOUT', '120'))

# Keepalive 时间 - 保持连接的秒数，用于复用连接
keepalive = int(os.getenv('KEEPALIVE', '5'))

# 进程名称 - 系统中显示的进程名
proc_name = "fastapiserver-gunicorn"

# 访问日志输出位置 - "-" 表示输出到 stdout（标准输出）
accesslog = "-"

# 错误日志输出位置 - "-" 表示输出到 stderr（标准错误）
errorlog = "-"

# 日志级别 - debug/info/warning/error/critical
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# 优雅关闭超时时间 - 收到关闭信号后等待多少秒再强制关闭 worker
graceful_timeout = int(os.getenv('GRACEFUL_TIMEOUT', '30'))

# 预加载应用代码 - true 表示启动时就加载代码（节省内存，性能好）；false 表示 worker 启动时才加载（支持热重载）
preload_app = os.getenv('PRELOAD_APP', 'true').lower() == 'true'

# 单个 Worker 最大请求数 - 处理多少请求后自动重启 worker，防止内存泄漏
max_requests = int(os.getenv('MAX_REQUESTS', '10000'))

# 最大请求随机抖动 - 给 max_requests 添加随机值，避免所有 worker 同时重启
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', '1000'))

# Worker 临时目录 - Uvicorn 特定配置，使用共享内存提升性能，Linux 用 /dev/shm，macOS 用 /tmp
# 自动检测系统可用的临时目录
if os.path.exists('/dev/shm'):
    worker_tmp_dir = os.getenv('WORKER_TMP_DIR', '/dev/shm')
else:
    worker_tmp_dir = os.getenv('WORKER_TMP_DIR', '/tmp')


def when_ready(server):
    """服务启动完成时的回调"""
    env = os.getenv('ENVIRONMENT')
    server.log.info(f"server 启动成功！环境={env}, 监听={bind}, workers={workers}")


def worker_int(worker):
    """Worker 收到中断信号时的回调"""
    worker.log.info(f"Worker {worker.pid} 收到中断信号，正在关闭...")


def post_fork(server, worker):
    """Worker fork 后的回调"""
    worker.log.info(f"Worker {worker.pid} 已启动")
