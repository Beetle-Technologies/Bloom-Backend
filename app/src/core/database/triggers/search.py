from sqlalchemy import DDL

PRODUCT_SEARCH_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, '');
    NEW.search_vector := to_tsvector('english', NEW.search_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

PRODUCT_SEARCH_TRIGGER = DDL(
    """
CREATE OR REPLACE TRIGGER product_search_update
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_vector();
"""
)

PRODUCT_ITEM_SEARCH_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION update_product_item_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, '');
    NEW.search_vector := to_tsvector('english', NEW.search_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

PRODUCT_ITEM_SEARCH_TRIGGER = DDL(
    """
CREATE OR REPLACE TRIGGER product_item_search_update
    BEFORE INSERT OR UPDATE ON product_items
    FOR EACH ROW
    EXECUTE FUNCTION update_product_item_search_vector();
"""
)
