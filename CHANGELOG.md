# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-05-20

### Added
- `src/scraping/linkedin.py`: Initial implementation for basic LinkedIn job scraping.
- `src/utils/orm_base.py`: SQLAlchemy model for `jobs_base_info` table and future tables.

### Changed
- `src/tools/`: Updated all tools (`browser_manager.py`, `database_manager.py`, `logging_manager.py`) to use Loguru for logging and SQLAlchemy for database management.
- Removed `src/utils/setup_database.py` (table creation now handled by `database_manager.py`).

## [0.2.0] - 2024-05-15

### Added
- New support files in the `src/tools` directory:
  - `browser_manager.py` for managing Selenium-based webdrivers.
  - `database_manager.py` for managing local database operations.
  - `logging_manager.py` for managing execution logs.
- Additional configurations in `poetry.toml`.

### Changed
- Minor updates to `README.md` and `.gitignore`.

## [0.1.0] - 2024-05-13

### Added
- Initial project structure including `src`, `tests`, `database`, and `docs` directories.
- Initial configuration files such as `pyproject.toml` and `.gitignore`.
- Initial base documentation including README, CONTRIBUTING, and other guides.
