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
DROP TRIGGER IF EXISTS product_search_update ON products;
CREATE TRIGGER product_search_update
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
DROP TRIGGER IF EXISTS product_item_search_update ON product_items;
CREATE TRIGGER product_item_search_update
    BEFORE INSERT OR UPDATE ON product_items
    FOR EACH ROW
    EXECUTE FUNCTION update_product_item_search_vector();
"""
)

COUNTRY_SEARCH_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION update_country_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := COALESCE(NEW.name, '');
    NEW.search_vector := to_tsvector('english', NEW.search_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

COUNTRY_SEARCH_TRIGGER = DDL(
    """
DROP TRIGGER IF EXISTS country_search_update ON country;
CREATE TRIGGER country_search_update
    BEFORE INSERT OR UPDATE ON country
    FOR EACH ROW
    EXECUTE FUNCTION update_country_search_vector();
"""
)

CURRENCY_SEARCH_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION update_currency_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_text := COALESCE(NEW.code, '') || ' ' || COALESCE(NEW.name, '');
    NEW.search_vector := to_tsvector('english', NEW.search_text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

CURRENCY_SEARCH_TRIGGER = DDL(
    """
DROP TRIGGER IF EXISTS currency_search_update ON currency;
CREATE TRIGGER currency_search_update
    BEFORE INSERT OR UPDATE ON currency
    FOR EACH ROW
    EXECUTE FUNCTION update_currency_search_vector();
"""
)
