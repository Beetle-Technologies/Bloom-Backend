from sqlmodel import DDL

AUDIT_LOG_TRIGGER_FUNCTION = DDL(
    """
DROP FUNCTION IF EXISTS create_audit_log() CASCADE;
CREATE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (account_id, action, resource_type, resource_id, details)
    VALUES (
        CASE
            WHEN TG_TABLE_NAME = 'accounts' THEN COALESCE(NEW.id, OLD.id)
            ELSE COALESCE(NEW.account_id, NEW.created_by, NEW.supplier_account_id, OLD.account_id, OLD.created_by, OLD.supplier_account_id)
        END,
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
