-- Create user roles
create role app_user nologin;

grant usage on schema api to app_user;
-- grant select on api.todos to app_user;
grant select on all tables in schema api to app_user;

create role authenticator noinherit login password 'r4Q*^LgBXd';
grant app_user to authenticator;


-- products view for api
-- https://stackoverflow.com/a/15261367
CREATE VIEW api.products AS
SELECT
    p.*,
    i.images,
    v.variants
FROM data.products p
INNER JOIN(
    SELECT
        product_id,
        array_agg(product_images.*) AS images
    FROM data.product_images
    GROUP BY product_id
) i USING (product_id)
INNER JOIN(
    SELECT
        product_id,
        array_agg(product_variants.*) AS variants
    FROM data.product_variants
    GROUP BY product_id
) v USING (product_id);


-- outfits view for api
CREATE VIEW api.outfits AS
SELECT
    *
FROM data.outfits
INNER JOIN (
    SELECT
        outfit_id,
        array_agg(t1.*) as images
    FROM data.outfit_images t1
    GROUP BY outfit_id
) t3 USING (outfit_id)
INNER JOIN (
    SELECT
        t1.outfit_id,
        json_agg(t2.*) as products
    FROM data.outfit_products t1
    INNER JOIN api.products t2 USING (product_id)
    GROUP BY outfit_id
) t2 USING (outfit_id)


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

SELECT pivot_value(10, 'base_color');

-- Drop or truncate all tables and views in correct order
drop if exists view api.products,
                    api.outfits;
drop table if exists data.products,
                     data.product_images,
                     data.product_variants,
                     data.entity,
                     data.outfits,
                     data.outfit_images,
                     data.outfit_products,
                     data.liked_entity,
                     data.users,
                     data.trained_recommendation_models;

-- Indexes
-- Index naming conventions: https://gist.github.com/popravich/d6816ef1653329fb1745
CREATE INDEX product_images_product_id_idx
ON data.product_images (product_id);

CREATE INDEX product_variants_product_id_idx
ON data.product_variants (product_id);
