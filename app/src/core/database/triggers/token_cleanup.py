from sqlmodel import DDL

TOKEN_CLEANUP_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete tokens that are revoked and past their deleted_datetime
    DELETE FROM tokens
    WHERE revoked = TRUE
    AND deleted_datetime IS NOT NULL
    AND deleted_datetime < NOW();

    -- Also delete tokens that are expired (past deleted_datetime) even if not explicitly revoked
    DELETE FROM tokens
    WHERE deleted_datetime IS NOT NULL
    AND deleted_datetime < NOW();

    RETURN NULL;
END;
$$ language 'plpgsql';
"""
)

TOKEN_CLEANUP_TRIGGER = DDL(
    """
CREATE TRIGGER token_cleanup_trigger
    AFTER UPDATE OF revoked ON tokens
    FOR EACH STATEMENT EXECUTE FUNCTION cleanup_expired_tokens();
"""
)

# Also create a scheduled trigger that runs periodically
TOKEN_CLEANUP_SCHEDULED_TRIGGER = DDL(
    """
CREATE OR REPLACE FUNCTION scheduled_token_cleanup()
RETURNS void AS $$
BEGIN
    -- Delete tokens that are revoked and past their deleted_datetime
    DELETE FROM tokens
    WHERE revoked = TRUE
    AND deleted_datetime IS NOT NULL
    AND deleted_datetime < NOW();

    -- Also delete tokens that are expired (past deleted_datetime) even if not explicitly revoked
    DELETE FROM tokens
    WHERE deleted_datetime IS NOT NULL
    AND deleted_datetime < NOW();
END;
$$ language 'plpgsql';
"""
)
