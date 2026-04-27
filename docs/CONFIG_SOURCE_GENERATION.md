# Config File Test Generation

TestQL now supports generating shell test scenarios from configuration files including Makefile, Taskfile.yml, docker-compose.yml, and buf.yaml.

## Usage

### Generate from Makefile

```bash
testql generate-ir --from makefile:./Makefile --to testtoon
testql generate-ir --from config:./Makefile --to testtoon
```

### Generate from Taskfile.yml

```bash
testql generate-ir --from taskfile:./Taskfile.yml --to testtoon
testql generate-ir --from config:./Taskfile.yml --to testtoon
```

### Generate from docker-compose.yml

```bash
testql generate-ir --from docker-compose:./docker-compose.yml --to testtoon
testql generate-ir --from config:./docker-compose.yml --to testtoon
```

### Generate from buf.yaml

```bash
testql generate-ir --from buf:./buf.yaml --to testtoon
testql generate-ir --from config:./buf.yaml --to testtoon
```

### Output to file

```bash
testql generate-ir --from makefile:./Makefile --to testtoon --out generated.testql.toon.yaml
```

## Supported Source Types

- `makefile` - GNU Make build files
- `taskfile` - Task runner configuration
- `docker-compose` - Docker Compose service definitions
- `buf` - Protobuf/buf configuration
- `config` - Auto-detects file type based on filename

## How It Works

The config source parser:

1. **Parses the configuration file** - Extracts targets, tasks, services, or commands
2. **Filters commands** - Removes multi-line commands, template variables, and echo statements
3. **Generates shell steps** - Creates ShellStep objects with filtered commands
4. **Adds assertions** - Includes exit code and output error checks
5. **Renders to TestTOON** - Outputs TestQL scenario in TestTOON YAML format

## Example Output

```yaml
# SCENARIO: Makefile tests
# TYPE: shell

CONFIG[3]{key, value}:
  project_dir, /path/to/project
  timeout_ms, 60000
  fail_fast, False

SHELL[3]{command, exit_code}:
  cd /path/to/project && make validate, 0
  cd /path/to/project && make build, 0
  cd /path/to/project && make test, 0

ASSERT[2]{field, operator, expected}:
  exit_code, ==, 0
  output, not_contains, Error
```

## Command Filtering

The generator automatically filters out:

- Multi-line commands (containing newlines or semicolons)
- Template variables ({{...}})
- Simple echo statements (unless validation-related)
- Empty commands after cleaning

## Running Generated Tests

```bash
# Run generated scenario
testql run generated.testql.toon.yaml

# Dry run (validate without executing)
testql run generated.testql.toon.yaml --dry-run
```

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: Generate config tests
  run: |
    testql generate-ir --from makefile:./Makefile --to testtoon --out config-tests.testql.toon.yaml

- name: Run config tests
  run: |
    testql run config-tests.testql.toon.yaml
```

## Implementation Details

The implementation adds:

- `testql/generators/sources/config_source.py` - ConfigSource class with parsers
- Lazy-loaded registration in `testql/generators/sources/__init__.py`
- Support for Makefile (including .mk includes), Taskfile.yml, docker-compose.yml, buf.yaml

## Future Enhancements

Potential additions:

- Shell script (.sh) parsing
- Infrastructure as Code (Terraform, Kubernetes manifests)
- CI configuration files (GitHub Actions, GitLab CI)
- Package managers (package.json, requirements.txt)
