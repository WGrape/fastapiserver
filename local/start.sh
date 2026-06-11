#!/usr/bin/env bash
# =============================================================================
# 本地环境启动脚本
# 使用方法：
#   cd /path/to/project
#   chmod +x local/start.sh
#   local/start_in_docker.sh [--mode=uvicorn|gunicorn]
#
# 参数说明：
#   --mode=uvicorn   : 使用 uvicorn 启动（支持热重载）
#   --mode=gunicorn  : 使用 gunicorn 启动（默认）
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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

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
# 1. 处理命令行参数
# =============================================================================
info "[1] 命令行参数处理..."

# 定义默认参数
MODE="gunicorn"

# 解析命令行参数
for arg in "$@"; do
    case $arg in
        --mode=*)
            MODE="${arg#*=}"
            shift
            ;;
        *)
            # 未知参数
            ;;
    esac
done

# 检查命令行参数
if [ "$MODE" != "uvicorn" ] && [ "$MODE" != "gunicorn" ]; then
    error "未知的启动模式: $MODE"
    error "使用方法: $0 [--mode=gunicorn|uvicorn]"
    exit 1
fi

# 打印命令行参数
debug "mode=$MODE"

info "命令行参数处理完成！"
info ""

# =============================================================================
# 2. 进入项目根目录
# =============================================================================
info "[2] 进入项目根目录"
cd "$PROJECT_ROOT"
debug "已进入项目根目录，当前项目路径: $(pwd)"
info ""

# =============================================================================
# # 3. 检查 Python 版本
# =============================================================================
info "[3] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    error "未找到 python3，请先安装 Python 3.11 或更高版本"
    exit 1
fi

# 检查版本是否满足要求
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
debug "检测到 Python 版本: $PYTHON_VERSION"
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    error "需要 Python 3.11 或更高版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

info "Python 版本检查通过！"
info ""

# =============================================================================
# 4. 创建虚拟环境（如果不存在）
#  虚拟环境什么版本呢 ？其实执行 python3 -m venv venv 中的 python3 就决定了虚拟环境的版本。
#  如果你想用某个特定版本创建虚拟环境，可以用完整路径，例如：
#  # 使用 Python 3.11
#  /usr/local/bin/python3.11 -m venv venv
#  # 或使用 Python 3.12
#  /opt/homebrew/bin/python3.12 -m venv venv
#  虚拟环境初始化完成！常用命令：
#    - 退出虚拟环境: deactivate
#    - 删除虚拟环境: rm -rf venv
# =============================================================================
info "[4] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    debug "创建虚拟环境..."
    debug "如果是在命令行中执行python3 -m venv venv会自动创建虚拟环境，如果IDE无法识别，所以需要在IDE设置中为此项目新建一个venv类型的Python解释器，路径指向 $PROJECT_ROOT/venv"
    debug "=======================python3 -m venv venv======================="
    debug "使用 Python $PYTHON_VERSION 创建虚拟环境..."
    python3 -m venv venv
    debug "虚拟环境创建完成，版本: $(venv/bin/python --version)"
else
    debug "虚拟环境已存在，版本: $(venv/bin/python --version)"
fi

# 激活虚拟环境
debug "已激活虚拟环境"
source venv/bin/activate
info ""

# =============================================================================
# 5. 安装依赖
# =============================================================================
info "[5] 安装 Python 依赖..."
debug "当前的 Python 版本: $(which python) ($(python --version))"

# 处理 SSL 证书问题 - 信任 PyPI 源
# 这将允许 pip 在安装依赖时忽略 SSL 证书验证错误，否则可能会因为证书问题导致安装报错 ：
# WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)'))': /simple/pip/
PIP_TRUSTED_HOSTS="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
pip install $PIP_TRUSTED_HOSTS --upgrade pip
pip install $PIP_TRUSTED_HOSTS -r requirements.txt

info "依赖安装完成！"
info ""

# =============================================================================
# 6. 加载环境变量
# =============================================================================
info "[6] 开始加载环境变量..."
ENV_FILE="$PROJECT_ROOT/deploy/dev/docker-deploy.env"
if [ -f "$ENV_FILE" ]; then
    # 导出环境变量（忽略注释和空行）
    set -a
    source <(grep -v '^#' "$ENV_FILE" | grep -v '^$')
    set +a
    debug "已从 $ENV_FILE 加载环境变量"
    debug "HOST=${HOST:-0.0.0.0}, PORT=${PORT:-8000}, WORKERS=${WORKERS:-1}"
else
    warn "未找到环境变量文件: $ENV_FILE"
fi

info "环节变量加载完成！"
info ""

# =============================================================================
# 7. 启动服务
# =============================================================================
info "[7] 开始启动服务..."
if [ "$MODE" = "uvicorn" ]; then
    debug "使用 Uvicorn 启动（支持热重载）"
    debug "命令: uvicorn src.cmd.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload"
    # 使用 uvicorn 启动，支持热重载
    uvicorn src.cmd.main:app \
        --host "${HOST:-0.0.0.0}" \
        --port "${PORT:-8000}" \
        --reload
elif [ "$MODE" = "gunicorn" ]; then
    debug "使用 Gunicorn 启动"
    debug "命令: gunicorn src.cmd.main:app -c $PROJECT_ROOT/deploy/gunicorn_config.py"
    # 使用 gunicorn 启动
    gunicorn src.cmd.main:app \
        -c "$PROJECT_ROOT/deploy/gunicorn_config.py"
else
    error "未知的启动模式: $MODE，请使用 --mode=uvicorn 或 --mode=gunicorn"
fi
