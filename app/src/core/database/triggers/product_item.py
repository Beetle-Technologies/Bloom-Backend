from sqlalchemy import DDL

PRODUCT_ITEM_TRIGGER_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION populate_product_item_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Only populate fields if they are NULL (allows manual overrides)

    -- Copy name from product if not provided
    IF NEW.name IS NULL THEN
        SELECT name INTO NEW.name FROM products WHERE id = NEW.product_id;
    END IF;

    -- Copy description from product if not provided
    IF NEW.description IS NULL THEN
        SELECT description INTO NEW.description FROM products WHERE id = NEW.product_id;
    END IF;

    -- Calculate price from product price + markup if not provided
    IF NEW.price IS NULL THEN
        SELECT price + (price * NEW.markup_percentage / 100)
        INTO NEW.price
        FROM products
        WHERE id = NEW.product_id;
    END IF;

    -- Copy currency_id from product if not provided
    IF NEW.currency_id IS NULL THEN
        SELECT currency_id INTO NEW.currency_id FROM products WHERE id = NEW.product_id;
    END IF;

    -- Copy category_id from product if not provided
    IF NEW.category_id IS NULL THEN
        SELECT category_id INTO NEW.category_id FROM products WHERE id = NEW.product_id;
    END IF;

    -- Copy status from product if not provided
    IF NEW.status IS NULL THEN
        SELECT status INTO NEW.status FROM products WHERE id = NEW.product_id;
    END IF;

    -- Copy is_digital from product if not provided
    IF NEW.is_digital IS NULL THEN
        SELECT is_digital INTO NEW.is_digital FROM products WHERE id = NEW.product_id;
    END IF;

    -- Merge attributes with product attributes if not provided
    IF NEW.attributes IS NULL THEN
        SELECT attributes INTO NEW.attributes FROM products WHERE id = NEW.product_id;
    ELSE
        -- If attributes are provided, merge them with product attributes
        -- Custom attributes override product attributes
        SELECT
            COALESCE(p.attributes, '{}'::jsonb) || COALESCE(NEW.attributes, '{}'::jsonb)
        INTO NEW.attributes
        FROM products p
        WHERE p.id = NEW.product_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

PRODUCT_ITEM_TRIGGER = DDL(
    """
CREATE OR REPLACE TRIGGER product_item_populate_fields
    BEFORE INSERT OR UPDATE ON product_items
    FOR EACH ROW
    EXECUTE FUNCTION populate_product_item_fields();
"""
)


PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_FUNCTION = DDL(
    """
CREATE OR REPLACE FUNCTION update_product_items_on_product_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Update all product item prices when the product price changes
    -- Only update items that don't have custom prices (price was calculated from markup)
    IF OLD.price != NEW.price THEN
        UPDATE product_items
        SET price = NEW.price + (NEW.price * markup_percentage / 100),
            updated_datetime = NOW()
        WHERE product_id = NEW.id
        AND (
            -- Only update items where price appears to be calculated (not custom)
            -- We identify calculated prices by checking if they match the old calculated value
            price = OLD.price + (OLD.price * markup_percentage / 100)
            OR price IS NULL
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

PRODUCT_ITEM_PRICE_UPDATE_VIA_PRODUCT_TRIGGER = DDL(
    """
CREATE OR REPLACE TRIGGER product_price_update_items
    AFTER UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_items_on_product_price_change();
"""
)
