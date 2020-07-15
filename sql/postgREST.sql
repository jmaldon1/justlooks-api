-- Create user roles
create role app_user nologin;

grant usage on schema api to app_user;
-- grant select on api.todos to app_user;
grant select on all tables in schema api to app_user;

create role authenticator noinherit login password 'r4Q*^LgBXd';
grant app_user to authenticator;


-- Products materialized view (view is stored on disk)
-- We need to refresh this view to update the data
CREATE MATERIALIZED VIEW api.products AS
SELECT
    p.*,
    i.images,
    v.variants
FROM data.products p
JOIN(
    SELECT
        product_id,
        json_agg(product_images.*) AS images
    FROM data.product_images
    GROUP BY product_id
) i ON i.product_id = p.product_id
JOIN(
    SELECT
        product_id,
        json_agg(product_variants.*) AS variants
    FROM data.product_variants
    GROUP BY product_id
) v ON v.product_id = p.product_id;

-- Update materialized view
REFRESH MATERIALIZED VIEW api.products;

-- Get pivot value for seek pagination
CREATE OR REPLACE FUNCTION api.pivot_value(int_id int, col text)
  RETURNS text AS $body$
DECLARE
    pivot_val text;
BEGIN
    EXECUTE format ($$
        SELECT %I
        FROM api.products
        WHERE int_id = %s
        $$, col, int_id)
    INTO pivot_val;
    RETURN pivot_val;
END;
$body$ LANGUAGE plpgsql STABLE;

SELECT pivot_value(10, 'base_color')

-- Drop or truncate all tables in correct order
drop table  api.products,
            api.product_images,
            api.product_variants,
            api.entity,
            api.outfits,
            api.outfit_images,
            api.outfit_products,
            api.liked_entity,
            api.users,
            api.trained_recommendation_models