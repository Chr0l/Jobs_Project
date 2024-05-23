# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2024-05-22

### Fixed
- **Improved Location and Work Format Handling in LinkedIn Scraper**: Fixed an issue in `src\scraping\linkedin.py` where an error was generated when the work format was not provided in the LinkedIn job listings.
- **Page Navigation Fix**: Resolved an issue in `src\scraping\linkedin.py` where the action button of a card was mistakenly clicked instead of the next page button, causing an infinite loop on the same page.
- **Reliable Action Button Detection**: Fixed an intermittent problem where the action button on job cards was not being located, as reported in `src\scraping\linkedin.py`.

## [0.3.1] - 2024-05-22

### Added
- `main.py`: Added the `main.py` file with the `EnvironmentManager` class to manage environment setup, including creation and validation of the `.env` file, secret key, and database configuration.
- `src\utils\orm_base.py`: Added `User` and `Account` tables to store user and account information, with support for password encryption.

### Changed
- `src\tools\database_manager.py`: Modified to support multiple tables, not just the `JobsBaseInfo` table, allowing for generic CRUD operations.
- `src\utils\orm_base.py`: Improved the `JobsBaseInfo` table structure and added methods for handling passwords and cookies.
- `src\tools\browser_manager.py`: Changed cookie management to store cookies in the database instead of local files.
- `src\scraping\linkedin.py`: Adjusted to correctly use user data and cookies stored in the database instead of local files or environment variables.
- `README.md`: Changed to display supported platforms

### Fixed
- **Job name duplication issue**: Fixed an issue that resulted in job name text duplication during data collection. 
- **Separation of location and job type**: We adjusted the data analysis logic in our extraction script to clearly separate location and job type information in the collected job data.


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
