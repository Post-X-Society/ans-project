#!/bin/bash

##############################################################################
# Infrastructure Health Check Script
#
# Purpose: Verify all Docker services are healthy and accessible
# Usage: ./scripts/health-check.sh
# Exit: 0 if all healthy, 1 if any failures
#
# Created: 2025-12-14
# Author: DevOps/QA Engineer
##############################################################################

set -e  # Exit on any error in strict mode (disabled for health checks)
set +e  # Allow commands to fail so we can report them

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Project root (assuming script is in scripts/ directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/infrastructure/docker-compose.dev.yml"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_check() {
    echo -e "\n${YELLOW}→${NC} $1"
}

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

##############################################################################
# Health Check Functions
##############################################################################

check_docker_running() {
    print_check "Checking if Docker is running..."
    if docker info >/dev/null 2>&1; then
        pass "Docker daemon is running"
        return 0
    else
        fail "Docker daemon is not running"
        return 1
    fi
}

check_docker_compose() {
    print_check "Checking Docker Compose version..."
    local version=$(docker compose version 2>&1)
    if [ $? -eq 0 ]; then
        pass "Docker Compose is available: $version"
        return 0
    else
        fail "Docker Compose is not available"
        return 1
    fi
}

check_services_running() {
    print_check "Checking if all Docker services are running..."

    cd "$PROJECT_ROOT"
    local services=("postgres" "redis" "backend" "frontend")
    local all_running=0

    for service in "${services[@]}"; do
        local status=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.State}}" 2>/dev/null)
        if [ "$status" = "running" ]; then
            pass "Service '$service' is running"
        else
            fail "Service '$service' is NOT running (status: $status)"
            all_running=1
        fi
    done

    return $all_running
}

check_service_health() {
    print_check "Checking Docker service health status..."

    cd "$PROJECT_ROOT"
    local healthy_services=("postgres" "redis" "backend")
    local all_healthy=0

    for service in "${healthy_services[@]}"; do
        local health=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.Health}}" 2>/dev/null)
        if [ "$health" = "healthy" ]; then
            pass "Service '$service' is healthy"
        else
            fail "Service '$service' health: $health"
            all_healthy=1
        fi
    done

    return $all_healthy
}

check_backend_health_endpoint() {
    print_check "Testing backend health endpoint..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>&1)

    if [ "$response" = "200" ]; then
        local health_json=$(curl -s http://localhost:8000/api/v1/health 2>&1)
        local status=$(echo "$health_json" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

        if [ "$status" = "healthy" ]; then
            pass "Backend health endpoint returns 200 OK with status: $status"
            return 0
        else
            fail "Backend health endpoint status: $status (expected: healthy)"
            return 1
        fi
    else
        fail "Backend health endpoint returned HTTP $response (expected: 200)"
        return 1
    fi
}

check_database_connectivity() {
    print_check "Testing PostgreSQL database connectivity..."

    local result=$(docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT 1;" 2>&1)

    if [ $? -eq 0 ]; then
        pass "Database accepts connections"
    else
        fail "Database connection failed: $result"
        return 1
    fi

    # Check pgvector extension
    local vector_result=$(docker exec ans-postgres psql -U postgres -d ans_dev -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>&1)

    if echo "$vector_result" | grep -q "vector"; then
        local version=$(echo "$vector_result" | grep "vector" | awk '{print $3}')
        pass "pgvector extension installed (version: $version)"
        return 0
    else
        fail "pgvector extension not found"
        return 1
    fi
}

check_redis_connectivity() {
    print_check "Testing Redis connectivity..."

    local pong=$(docker exec ans-redis redis-cli ping 2>&1)

    if [ "$pong" = "PONG" ]; then
        pass "Redis responds to PING"
        return 0
    else
        fail "Redis did not respond correctly: $pong"
        return 1
    fi
}

check_frontend_accessibility() {
    print_check "Testing frontend accessibility..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>&1)

    if [ "$response" = "200" ]; then
        pass "Frontend accessible on port 5173 (HTTP $response)"
        return 0
    else
        fail "Frontend returned HTTP $response (expected: 200)"
        return 1
    fi
}

check_backend_tests() {
    print_check "Running backend test suite..."

    local test_output=$(docker exec ans-backend pytest --tb=short -q 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        local passed=$(echo "$test_output" | grep -o "[0-9]* passed" | cut -d' ' -f1)
        pass "All backend tests passed ($passed tests)"
        return 0
    else
        local passed=$(echo "$test_output" | grep -o "[0-9]* passed" | cut -d' ' -f1)
        local failed=$(echo "$test_output" | grep -o "[0-9]* failed" | cut -d' ' -f1)
        fail "Backend tests failed: $passed passed, $failed failed"
        return 1
    fi
}

check_test_coverage() {
    print_check "Checking test coverage..."

    local coverage_output=$(docker exec ans-backend pytest --cov=app --cov-report=term-missing -q 2>&1)
    local coverage=$(echo "$coverage_output" | grep "TOTAL" | awk '{print $4}' | tr -d '%')

    if [ -n "$coverage" ]; then
        if [ "${coverage%.*}" -ge 80 ]; then
            pass "Test coverage: ${coverage}% (meets 80% requirement)"
            return 0
        else
            fail "Test coverage: ${coverage}% (below 80% requirement)"
            return 1
        fi
    else
        fail "Could not determine test coverage"
        return 1
    fi
}

check_api_endpoint() {
    print_check "Testing API endpoints..."

    # Test submissions endpoint (GET)
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/submissions 2>&1)

    if [ "$response" = "200" ]; then
        pass "API submissions endpoint accessible (HTTP $response)"
        return 0
    else
        fail "API submissions endpoint returned HTTP $response"
        return 1
    fi
}

##############################################################################
# Main Execution
##############################################################################

main() {
    print_header "Ans Project Infrastructure Health Check"
    echo "Project: $PROJECT_ROOT"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

    # Core infrastructure checks
    print_header "1. Docker Infrastructure"
    check_docker_running || true
    check_docker_compose || true

    # Service status checks
    print_header "2. Service Status"
    check_services_running || true
    check_service_health || true

    # Connectivity checks
    print_header "3. Service Connectivity"
    check_backend_health_endpoint || true
    check_database_connectivity || true
    check_redis_connectivity || true
    check_frontend_accessibility || true

    # API functionality checks
    print_header "4. API Functionality"
    check_api_endpoint || true

    # Testing checks
    print_header "5. Test Suite"
    check_backend_tests || true
    check_test_coverage || true

    # Summary
    print_header "Health Check Summary"
    echo ""
    echo "  Total Checks: $TOTAL_CHECKS"
    echo -e "  ${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "  ${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  ✓ All health checks passed!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}  ✗ Health checks failed!${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Please review the failed checks above and consult:"
        echo "  - docs/INFRASTRUCTURE_TESTING.md"
        echo "  - docs/TROUBLESHOOTING.md (when available)"
        echo "  - docs/POST_MORTEM_SSR_MIGRATION.md"
        echo ""
        exit 1
    fi
}

# Run main function
main
