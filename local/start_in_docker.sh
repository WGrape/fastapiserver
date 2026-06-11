#!/usr/bin/env bash
# =============================================================================
# 本地环境 Docker 启动脚本
# 使用方法：
#   cd /path/to/project
#   chmod +x local/start_in_docker.sh
#   local/start_in_docker.sh
# =============================================================================

# =============================================================================
# 全局初始化定义
# =============================================================================
set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 镜像名称
IMAGE_NAME="fastapiserver-image"
# 容器名称
CONTAINER_NAME="fastapiserver-container"

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# =============================================================================
# 1. 进入项目根目录
# =============================================================================
info "[1] 进入项目根目录"
cd "$PROJECT_ROOT"
debug "已进入项目根目录，当前项目路径: $(pwd)"
info ""

# =============================================================================
# 2. 检查 Docker
# =============================================================================
info "[2] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    error "Docker 未运行，请启动 Docker"
    exit 1
fi

info "检查 Docker 完成！"
info ""

# =============================================================================
# 3. 构建镜像（如不存在）
# =============================================================================
info "[3] 检查镜像是否存在..."
if ! docker image inspect "${IMAGE_NAME}" &> /dev/null; then
    debug "[3] 镜像不存在，开始构建..."
    docker build \
        -f "$PROJECT_ROOT/deploy/Dockerfile" \
        --build-arg ENVIRONMENT=dev \
        -t "${IMAGE_NAME}" \
        .
    debug "镜像构建完成"
else
    debug "镜像已存在"
fi

info "检查镜像完成！"
info ""

# =============================================================================
# 4. 停止并删除旧容器
# =============================================================================
info "[4] 停止并删除旧容器..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    info "清理旧容器..."
    docker rm -f "${CONTAINER_NAME}"
fi

info "容器清理完成！"
info ""

# =============================================================================
# 5. 启动容器
# =============================================================================
info "[5] 启动容器..."

docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "8000:8000" \
    --env-file "$PROJECT_ROOT/deploy/dev/docker-deploy.env" \
    -v "$PROJECT_ROOT/etc:/app/etc" \
    --restart unless-stopped \
    "${IMAGE_NAME}"

sleep 2

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    debug "已找到容器，容器启动正常"
else
    error "启动失败，请查看日志: docker logs ${CONTAINER_NAME}"
    exit 1
fi

info "容器启动完成！"
info ""
