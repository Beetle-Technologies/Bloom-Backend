from sqlmodel import DDL

AUDIT_LOG_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (account_id, action, resource_type, resource_id, details)
    VALUES (
        COALESCE(NEW.account_id, NEW.created_by, OLD.account_id),
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW))
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';
"""
)


ACCOUNT_AUDIT_LOG_TRIGGER = DDL(
    """
DROP TRIGGER IF EXISTS audit_accounts_trigger ON accounts;
CREATE TRIGGER audit_accounts_trigger
    AFTER INSERT OR UPDATE OR DELETE ON accounts
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();
"""
)

PRODUCT_AUDIT_LOG_TRIGGER = DDL(
    """
DROP TRIGGER IF EXISTS audit_products_trigger ON products;
CREATE TRIGGER audit_products_trigger
    AFTER INSERT OR UPDATE OR DELETE ON products
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();
"""
)
