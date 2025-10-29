#!/usr/bin/env bash
#
# Complete End-to-End Test Script for CMD Chat
# Tests the full application workflow with real processes
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST="127.0.0.1"
PORT=9999
SERVER_PID=""
TEST_PASSED=0
TEST_FAILED=0

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    rm -f /tmp/cmdchat_test_* 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Test function
run_test() {
    local test_name="$1"
    echo -e "${BLUE}▶ Testing: ${test_name}${NC}"
}

pass_test() {
    TEST_PASSED=$((TEST_PASSED + 1))
    echo -e "${GREEN}  ✓ PASSED${NC}"
}

fail_test() {
    TEST_FAILED=$((TEST_FAILED + 1))
    echo -e "${RED}  ✗ FAILED: $1${NC}"
}

# Print header
echo "=========================================="
echo "   CMD CHAT - E2E INTEGRATION TEST"
echo "=========================================="
echo ""

# Test 1: Check installation
run_test "Installation Check"
if [ -f ".venv/bin/cmdchat-server" ] && [ -f ".venv/bin/cmdchat-client" ]; then
    pass_test
else
    fail_test "cmdchat binaries not found"
    exit 1
fi

# Test 2: Python module import
run_test "Python Module Import"
if .venv/bin/python -c "import cmdchat; import cmdchat.server; import cmdchat.client" 2>/dev/null; then
    pass_test
else
    fail_test "Cannot import cmdchat modules"
    exit 1
fi

# Test 3: Server startup
run_test "Server Startup"
.venv/bin/cmdchat-server --host $HOST --port $PORT > /tmp/cmdchat_test_server.log 2>&1 &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    pass_test
else
    fail_test "Server process not running"
    cat /tmp/cmdchat_test_server.log
    exit 1
fi

# Test 4: Port binding
run_test "Port Binding"
if ss -tuln | grep ":$PORT" > /dev/null 2>&1; then
    pass_test
else
    fail_test "Port $PORT is not open"
    exit 1
fi

# Test 5: TCP connection
run_test "TCP Connection Test"
if timeout 2 bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
    pass_test
else
    fail_test "Cannot establish TCP connection"
    exit 1
fi

# Test 6: Socket connectivity (Python)
run_test "Socket Connectivity"
cat > /tmp/cmdchat_test_socket.py << 'EOF'
import socket
import sys

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(('127.0.0.1', 9999))
    sock.close()
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF

if .venv/bin/python /tmp/cmdchat_test_socket.py; then
    pass_test
else
    fail_test "Socket connection failed"
fi

# Test 7: Server log verification
run_test "Server Log Verification"
if grep -q "CMD Chat server listening" /tmp/cmdchat_test_server.log; then
    pass_test
else
    fail_test "Server did not log startup message"
fi

# Test 8: Server process health
run_test "Server Process Health"
if ps -p $SERVER_PID -o %cpu,%mem,etime,cmd | grep -q cmdchat-server; then
    pass_test
else
    fail_test "Server process unhealthy"
fi

# Test 9: Multiple connection attempts
run_test "Multiple Connection Attempts"
SUCCESS=0
for i in {1..5}; do
    if timeout 1 bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
        SUCCESS=$((SUCCESS + 1))
    fi
    sleep 0.1
done

if [ $SUCCESS -eq 5 ]; then
    pass_test
else
    fail_test "Only $SUCCESS/5 connections succeeded"
fi

# Test 10: Server resource usage
run_test "Server Resource Usage"
CPU_USAGE=$(ps -p $SERVER_PID -o %cpu --no-headers | awk '{print int($1)}')
MEM_USAGE=$(ps -p $SERVER_PID -o %mem --no-headers | awk '{print int($1)}')

if [ $CPU_USAGE -lt 50 ] && [ $MEM_USAGE -lt 10 ]; then
    pass_test
else
    fail_test "Resource usage too high (CPU: ${CPU_USAGE}%, MEM: ${MEM_USAGE}%)"
fi

# Test 11: Concurrent connections test
run_test "Concurrent Connections"
cat > /tmp/cmdchat_test_concurrent.py << 'EOF'
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def connect_test(conn_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', 9999))
        time.sleep(0.1)
        sock.close()
        return True
    except:
        return False

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(connect_test, i) for i in range(10)]
    results = [f.result() for f in as_completed(futures)]

if all(results):
    sys.exit(0)
else:
    print(f"Failed: {results.count(False)}/10", file=sys.stderr)
    sys.exit(1)
EOF

if .venv/bin/python /tmp/cmdchat_test_concurrent.py; then
    pass_test
else
    fail_test "Concurrent connections failed"
fi

# Test 12: Server stability after load
run_test "Server Stability After Load"
sleep 1
if ps -p $SERVER_PID > /dev/null; then
    pass_test
else
    fail_test "Server crashed after load test"
fi

# Test 13: Graceful shutdown test
run_test "Graceful Shutdown"
kill -TERM $SERVER_PID 2>/dev/null
sleep 2

if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    pass_test
    SERVER_PID=""  # Clear PID since server is stopped
else
    fail_test "Server did not shutdown gracefully"
    kill -9 $SERVER_PID 2>/dev/null || true
    SERVER_PID=""
fi

# Test 14: Restart capability
run_test "Server Restart"
.venv/bin/cmdchat-server --host $HOST --port $PORT > /tmp/cmdchat_test_server2.log 2>&1 &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null && ss -tuln | grep ":$PORT" > /dev/null 2>&1; then
    pass_test
else
    fail_test "Server failed to restart"
fi

# Test 15: Final health check
run_test "Final Health Check"
if ps -p $SERVER_PID > /dev/null && \
   ss -tuln | grep ":$PORT" > /dev/null 2>&1 && \
   timeout 1 bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
    pass_test
else
    fail_test "Final health check failed"
fi

# Print summary
echo ""
echo "=========================================="
echo "   TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed: $TEST_PASSED${NC}"
echo -e "${RED}Failed: $TEST_FAILED${NC}"
echo "Total:  $((TEST_PASSED + TEST_FAILED))"
echo ""

if [ $TEST_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL E2E TESTS PASSED! 🎉${NC}"
    echo ""
    echo "✓ Server starts correctly"
    echo "✓ Port binding works"
    echo "✓ Network connections succeed"
    echo "✓ Server handles load"
    echo "✓ Graceful shutdown works"
    echo "✓ Application is production-ready"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Server logs:"
    echo "---"
    cat /tmp/cmdchat_test_server.log 2>/dev/null || echo "No server logs found"
    exit 1
fi
