### <ins> Ongtrum </ins>

Ongtrum is a Python test runner designed for speed <br>

## <ins> Why Ongtrum is Fast ? </ins>

<ins> Scan </ins> <br>

Recursively scans for test files in the project directory with a Cython-optimized filesystem scanner <br>

<ins> Parse </ins> <br>

Each file is parsed with a Cython-optimized AST parser <br>

<ins> Execute </ins> <br>

For each file, all its test classes and methods are executed in one go using Python’s exec <br>
To reduce overhead, files are processed in batches, keeping worker processes alive throughout the run <br>

<ins> Optional Parallelism </ins> <br>

Tests can be run across multiple processes with `--workers` <br>

## <ins> Benchmark </ins>

Execution Commands: <br>

- Unittests: `python -m unittest discover <Project Dir>` <br>
- PyTest: `python -m pytest <Project Dir> -s -q` <br>
- Ongtrum: `python -m ongtrum.py' -q --project <Project Dir>` <br>

Test Files: 5440 <br>
Test Class:: 10880 <br>

- Unittests: 12.462s <br>
- PyTest: 27.217S <br>
- Ongtrum: 5.950s (vs Unittests 2 × Faster, vs PyTest 4.5 × Faster) <br>

[Ideas]

. Test Reporting & Analytics

HTML / PDF reports: Use libraries like pytest-html, allure-pytest for rich reports with screenshots and logs

Custom dashboards: Store test results in JSON or a database and visualize trends (failures, durations) with Plotly or Dash

Slack/Teams integration: Automatically send test results or alerts for failed tests.

2. Test Data Management

Data-driven testing: Pull test data from CSV, Excel, JSON, or databases.

Randomized test data: Use Faker to generate realistic test data dynamically.

Parameterization: Pytest fixtures or decorators to run the same test with multiple datasets.

3. Enhanced Logging & Debugging

Structured logging: Use loguru for better logging format and levels.

Screenshots on failure: Automatically capture screenshots when a test fails.

Video recording: Tools like seleniumbase allow recording test sessions for debugging.

4. Parallel Execution & Scaling

If already fast, consider:

Running tests across multiple environments (browsers, OS) with pytest-xdist or selenium-grid.

Integration with CI/CD pipelines (GitHub Actions, Jenkins, GitLab CI).

5. Test Maintenance & Reusability

Page Object Model / Component Object Model: Makes UI tests more maintainable.

Custom assertion library: Wrap assertions for clearer messages and reusability.

Reusable utilities: For API requests, DB connections, or common UI actions.

6. AI-assisted Features

Automatic locators: AI can suggest more stable locators for UI elements.

Test case suggestion: Generate additional test scenarios from previous failures or logs.

7. Security / API Testing

Add features for:

API contract verification (OpenAPI / Swagger validation)

Basic security checks (SQL injection, XSS)

Response time monitoring