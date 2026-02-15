-- WeChat QR login database objects
-- Target: MySQL 8.x
-- Note: keep all timestamps in UTC at application layer.
--
-- Execution guide:
-- 1) Backup database before applying schema changes.
-- 2) Execute in target DB:
--      mysql -h <host> -P <port> -u <user> -p <db> < backend/sql/wechat_auth_tables.sql
-- 3) Verify tables:
--      SHOW TABLES LIKE 'auth_%';
-- 4) Verify indexes:
--      SHOW INDEX FROM auth_user_identity;
--      SHOW INDEX FROM auth_login_session;
--
-- Data lifecycle guide:
-- - auth_user_identity stores long-lived provider binding records.
-- - auth_login_session stores short-lived scan sessions and one-time tickets.
-- - deleted_at follows soft-delete convention:
--     0 = active
--     >0 = deleted unix timestamp (seconds/millis by project convention)
--
-- Compatibility notes:
-- - IF NOT EXISTS is used, so rerun is idempotent for CREATE TABLE.
-- - Existing table shape mismatches are not auto-migrated by this script.
-- - For existing deployments with partial columns, run ALTER statements separately.
--
-- Security notes:
-- - provider_user_id should come from unionid when available, openid fallback.
-- - ticket column is unique to support one-time exchange semantics.
-- - do not store app secrets in DB tables.
--
-- ---------------------------------------------------------------------
-- Data dictionary: auth_user_identity
-- ---------------------------------------------------------------------
-- id:
--   bigint auto increment primary key.
-- user_id:
--   local user id in expenses_user.id.
-- provider:
--   provider key, currently "wechat".
-- provider_user_id:
--   stable third-party subject id (unionid preferred).
-- wechat_openid:
--   openid from WeChat OAuth response.
-- wechat_unionid:
--   unionid when account has unionid permission/scope.
-- nickname:
--   profile snapshot for display/debug.
-- avatar_url:
--   profile snapshot for display/debug.
-- raw_profile_json:
--   full profile snapshot for troubleshooting.
-- created_at / updated_at:
--   standard audit timestamps.
-- created_by / updated_by:
--   standard audit operators ("SYSTEM" for program writes).
-- deleted_at:
--   soft delete marker.
-- last_login_at:
--   last successful WeChat callback bind time.
--
-- Index rationale:
-- - uq_auth_user_identity_provider_user:
--   enforces one local binding per provider subject.
-- - idx_auth_user_identity_user_id:
--   supports reverse lookup by local user.
-- - idx_auth_user_identity_deleted_at:
--   speeds up active-row scans (deleted_at = 0).
--
-- ---------------------------------------------------------------------
-- Data dictionary: auth_login_session
-- ---------------------------------------------------------------------
-- session_id:
--   UUID string used by desktop polling endpoint.
-- channel:
--   login channel label, currently "wechat_qr".
-- state:
--   callback correlation key (signed by server).
-- status:
--   finite states: PENDING / CONFIRMED / EXPIRED / FAILED / CONSUMED.
-- user_id:
--   local user id after callback binding succeeds.
-- ticket:
--   short-lived one-time token for desktop exchange.
-- ticket_expires_at:
--   expiry for ticket consumption.
-- error_code / error_message:
--   failure detail written by callback/runtime handlers.
-- expires_at:
--   scan session expiry; after this no login should proceed.
-- created_at / updated_at:
--   standard audit timestamps.
-- created_by / updated_by:
--   standard audit operators.
-- deleted_at:
--   soft delete marker.
-- consumed_at:
--   set when ticket is consumed and status changes to CONSUMED.
--
-- Index rationale:
-- - uq_auth_login_session_state:
--   fast callback lookup + uniqueness.
-- - uq_auth_login_session_ticket:
--   prevent duplicated active ticket.
-- - idx_auth_login_session_status_exp:
--   session cleanup and polling queries.
-- - idx_auth_login_session_ticket_exp:
--   ticket validation path.
-- - idx_auth_login_session_deleted_at:
--   active-row filter acceleration.
--
-- ---------------------------------------------------------------------
-- Suggested cleanup policy (application/cron level)
-- ---------------------------------------------------------------------
-- 1) Periodically mark stale PENDING sessions to EXPIRED.
-- 2) Periodically soft-delete very old CONSUMED/FAILED/EXPIRED rows:
--      UPDATE ... SET deleted_at = UNIX_TIMESTAMP() WHERE ...
-- 3) Keep identity rows long-lived unless explicit account unlink action.
-- ---------------------------------------------------------------------

START TRANSACTION;

-- ---------------------------------------------------------------------
-- 1) Third-party identity binding table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_user_identity (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(50) NOT NULL,
  provider VARCHAR(32) NOT NULL,
  provider_user_id VARCHAR(128) NOT NULL,
  wechat_openid VARCHAR(128) NULL,
  wechat_unionid VARCHAR(128) NULL,
  nickname VARCHAR(128) NULL,
  avatar_url VARCHAR(512) NULL,
  raw_profile_json JSON NULL,

  -- system fields
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
  updated_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
  deleted_at BIGINT NOT NULL DEFAULT 0,

  last_login_at DATETIME NULL,
  UNIQUE KEY uq_auth_user_identity_provider_user (provider, provider_user_id),
  KEY idx_auth_user_identity_user_id (user_id),
  KEY idx_auth_user_identity_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2) QR login session table (state + one-time ticket)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_login_session (
  session_id CHAR(36) PRIMARY KEY,
  channel VARCHAR(32) NOT NULL,
  state CHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  user_id VARCHAR(50) NULL,
  ticket CHAR(64) NULL,
  ticket_expires_at DATETIME NULL,
  error_code VARCHAR(64) NULL,
  error_message VARCHAR(255) NULL,
  expires_at DATETIME NOT NULL,

  -- system fields
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
  updated_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
  deleted_at BIGINT NOT NULL DEFAULT 0,

  consumed_at DATETIME NULL,
  UNIQUE KEY uq_auth_login_session_state (state),
  UNIQUE KEY uq_auth_login_session_ticket (ticket),
  KEY idx_auth_login_session_status_exp (status, expires_at),
  KEY idx_auth_login_session_ticket_exp (ticket, ticket_expires_at),
  KEY idx_auth_login_session_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

COMMIT;
