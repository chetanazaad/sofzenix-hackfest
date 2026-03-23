-- ═══════════════════════════════════════════════════
--   Sofzenix HackFest — MySQL Database Setup
--   Run this ONCE before starting the server.
-- ═══════════════════════════════════════════════════
--
-- Usage in MySQL Workbench or command line:
--   mysql -u root -p < database_setup.sql
--
-- Or paste these commands into MySQL Workbench.

CREATE DATABASE IF NOT EXISTS sofzenix_hackfest
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE sofzenix_hackfest;

-- Note: Flask-SQLAlchemy will create all tables automatically
-- when you first start the server (python app.py).
-- You only need to run this file to CREATE the DATABASE.

SELECT 'Database sofzenix_hackfest is ready!' AS Status;
