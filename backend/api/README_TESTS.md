# API Service Integration Tests

This directory contains integration tests for the API service layer that use a **real MongoDB instance** instead of mocks.

## Why Integration Tests?

These tests verify that the API service works correctly with an actual MongoDB database, providing:
- Real database operations (queries, aggregations, sorting)
- Accurate validation of MongoDB queries
- Confidence that the code works in production-like conditions

## Prerequisites

**MongoDB must be running** before you can run these tests. The tests will automatically:
- Use a separate test database (`flights_scanner_test`)
- Clean up the test database before each test
- Not interfere with your production data

## Running the Tests

### Option 1: Using Docker Compose (Recommended)

Start the MongoDB container:

```bash
# Start all services (MongoDB, backend, frontend)
make docker-up

# Or start just MongoDB
docker-compose up -d mongodb
```

Then run the tests:

```bash
# Run API service tests only
make test-api

# Run all backend tests
make test

# Run with coverage report
make test-all
```

### Option 2: Using Local MongoDB

If you have MongoDB installed locally:

1. Ensure MongoDB is running on `localhost:27017`
2. Run the tests:

```bash
cd backend/api
python -m pytest test_api_service.py -v
```

### Option 3: Custom MongoDB Configuration

Set environment variables to point to your MongoDB instance:

```bash
export MONGO_HOST=your-mongo-host
export MONGO_PORT=27017
export MONGO_DATABASE=flights_scanner  # Test database will be flights_scanner_test

make test-api
```

## Test Coverage

The test suite includes **29 tests** covering all GET endpoints:

- ✅ **GET /flights** - 8 tests (filters, sorting, pagination)
- ✅ **GET /flights/{flight_id}** - 2 tests (found, not found)
- ✅ **GET /flights/stats/summary** - 2 tests
- ✅ **GET /airports/origins** - 2 tests
- ✅ **GET /airports/destinations** - 2 tests
- ✅ **GET /airports/routes** - 3 tests
- ✅ **GET /scans** - 3 tests
- ✅ **GET /scans/latest** - 2 tests
- ✅ **GET /flights/price-chart** - 3 tests
- ✅ **GET /health** - 2 tests

## What Gets Tested

Each test category verifies:

1. **Normal operations**: Standard queries return correct results
2. **Empty database**: Graceful handling of no data
3. **Filters**: Origin, destination, date range, price range
4. **Sorting**: Price ascending/descending, date, duration
5. **Pagination**: Correct page/page_size handling
6. **Aggregations**: Statistics, grouping, price calculations
7. **Case insensitivity**: Airport codes work in any case
8. **Error handling**: 404 for not found resources

## Troubleshooting

### Error: "Cannot connect to MongoDB!"

**Solution**: Start MongoDB before running tests:

```bash
make docker-up
# or
docker-compose up -d mongodb
```

### Error: Connection refused

**Cause**: MongoDB is not running or not accessible on the configured host/port.

**Solutions**:
1. Check MongoDB is running: `docker ps | grep mongo`
2. Check MongoDB logs: `docker-compose logs mongodb`
3. Verify connection settings in `.env` file
4. Test connection: `mongosh mongodb://localhost:8902` (or your configured port)

### Tests are slow

**Note**: These are integration tests that perform real database operations. They are slightly slower than unit tests with mocks, but provide much better confidence.

Typical run time: ~0.3-0.5 seconds for all 29 tests.

## Test Database

The tests use a **separate database** (`flights_scanner_test`) to avoid interfering with your production data.

Each test:
1. Drops the test database (clean slate)
2. Inserts sample data as needed
3. Runs assertions
4. The next test starts fresh

The test database is automatically cleaned up, so you don't need to manually manage it.

## Adding New Tests

When adding new endpoints or service methods:

1. Add test data fixtures in `test_api_service.py`
2. Create a test class for the new endpoint
3. Test normal operation, edge cases, and errors
4. Run tests to verify: `make test-api`

Example:

```python
class TestMyNewEndpoint:
    """Test my_new_endpoint service method."""

    def test_normal_operation(self, api_service, sample_data):
        """Test normal operation."""
        result = api_service.my_new_method()
        assert result is not None

    def test_empty_database(self, api_service):
        """Test with empty database."""
        result = api_service.my_new_method()
        assert result == []
```

## CI/CD Integration

To run these tests in CI/CD:

```yaml
# Example GitHub Actions / GitLab CI
services:
  mongodb:
    image: mongo:7.0
    ports:
      - 27017:27017

steps:
  - name: Run tests
    run: make test-api
    env:
      MONGO_HOST: localhost
      MONGO_PORT: 27017
```
