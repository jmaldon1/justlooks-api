import psycopg2
import pandas as pd
import itertools

from flask import request, jsonify

from api.routes import justlooks_api
# from api import trained_model, utils, constants


@justlooks_api.route("/n_recommended_outfits", methods=['GET'])
def n_recommended_outfits():
    user_id = request.args.get("user_id")
    n_query = request.args.get("n")
    if not user_id:
        return {"Error": "'user_id' argument is required"}
    
    if n_query:
        n = utils.__try_number(n_query)
    else:
        n = 10

    # TODO: Only select liked entities that were liked AFTER the last model training was done
    liked_entity_sql = """
        SELECT 
            int_id as liked_entity_id,
            entity_id,
            user_id
        FROM liked_entity
        WHERE user_id = %s
    """
    df_liked_entity = sql_to_pandas_df(liked_entity_sql, [(user_id,)])

    entity_sql = """
        SELECT 
            t1.int_id as entity_int_id,
            t1.entity_id,
            t2.int_id as outfit_int_id,
            t2.outfit ->> 'season' as season,
            t2.outfit ->> 'stylist' as stylist,
            t2.outfit ->> 'max_images' as max_images,
            t3.int_id as product_int_id,
            t3.product ->> 'fit' as fit,
            t3.product ->> 'name' as name,
            t3.product ->> 'brand' as brand,
            t3.product ->> 'color' as color,
            t3.product ->> 'style' as style,
            t3.product ->> 'corpus' as corpus,
            t3.product ->> 'gender' as gender,
            t3.product ->> 'images' as images,
            t3.product ->> 'category' as category,
            t3.product ->> 'material' as material,
            t3.product ->> 'occasion' as occasion,
            t3.product ->> 'variants' as variants,
            t3.product ->> 'available' as available,
            t3.product ->> 'published' as published,
            t3.product ->> 'base_color' as base_color,
            t3.product ->> 'shopify_id' as shopify_id,
            t3.product ->> 'waist_rise' as waist_rise,
            t3.product ->> 'product_url' as product_url,
            t3.product ->> 'brand_handle' as brand_handle,
            t3.product ->> 'last_updated' as last_updated,
            t3.product ->> 'product_type' as product_type,
            t3.product ->> 'product_features' as product_features
        FROM entity t1
        LEFT OUTER JOIN outfits t2 ON t1.entity_id = t2.outfit_id
        LEFT OUTER JOIN products_with_variants t3 ON t1.entity_id = t3.product_id
        WHERE entity_id IN %s
    """
    liked_entity_ids = tuple(df_liked_entity['entity_id'])
    if not liked_entity_ids:
        return {"Error": "User has not liked any items"}

    df_entity_merged_with_outfits_and_products = sql_to_pandas_df(entity_sql, [liked_entity_ids])

    # print(df_entity_merged_with_outfits_and_products)
    user_sql = """
        SELECT
            int_id as users_int_id,
            user_id
        FROM public.users
        WHERE user_id = %s
    """

    df_users = sql_to_pandas_df(user_sql, [(user_id,)])
    # print(df_users)
    users_int_id = int(df_users['users_int_id'])

    user_feature_names_with_weights = {
        # Product features
    #     "fit":          {"weight": 1},
        "name":         {"weight": 1},
    #     "brand":        {"weight": 1},
    #     "color":        {"weight": 1},
    #     "style":        {"weight": 1},
    #     "gender":       {"weight": 1},
    #     "category":     {"weight": 1},
    #     "material":     {"weight": 1},
    #     "occasion":     {"weight": 1},
    #     "base_color":   {"weight": 1},
    #     "waist_rise":   {"weight": 1},
    #     "product_type": {"weight": 1},
    #     "full_product": {"weight": 1},
        # Outfits features
        "stylist":      {"weight": 1},
    #     "season":       {"weight": 1},
    }

    single_df_users_with_features = create_user_features(df_liked_entity,
                                                         df_entity_merged_with_outfits_and_products,
                                                         df_users,
                                                         user_feature_names_with_weights,
                                                         specify_user_weights=True,
                                                         users_int_id=users_int_id)

    single_exploded_users_features_with_weights = single_df_users_with_features.explode('features_with_weights')[['user_id',
                                                                                                                  'users_int_id',
                                                                                                                  'features_with_weights']]
    
    single_exploded_users_features_with_weights['features_with_weights_with_int_id'] = generate_feature_with_int_id(single_exploded_users_features_with_weights,
                                                                                                                    'users_int_id',
                                                                                                                    features_col='features_with_weights')
    
    model_info = trained_model.model_info
    dataset = model_info['dataset_pickle']
    single_user_features_lightfm = dataset.build_user_features(single_exploded_users_features_with_weights['features_with_weights_with_int_id'])

    not_yet_liked_outfit_entity_ids_sql = """
    -- Select all entity ids that the user did not already like
    SELECT
        entity.entity_id,
        entity.int_id AS entity_int_id
    FROM outfits o
    INNER JOIN entity ON outfit_id = entity.entity_id
    WHERE NOT EXISTS (
        SELECT
        FROM liked_entity
        INNER JOIN outfits ON entity_id = outfits.outfit_id
        WHERE user_id = %s
        AND outfit_id = o.outfit_id
    );
    """
    df_not_yet_liked_outfit_entity_ids = sql_to_pandas_df(not_yet_liked_outfit_entity_ids_sql, [(user_id,)])

    item_features_lightfm = model_info['item_features_pickle']

    entity_ids_to_recommend = recommend_outfits(model_info['model_pickle'],
                                                users_int_id,
                                                df_not_yet_liked_outfit_entity_ids,
                                                single_user_features_lightfm,
                                                item_features_lightfm)
    
    outfit_ids_to_recommend = list(entity_ids_to_recommend['entity_id'])

    return jsonify(outfit_ids_to_recommend[0:n])












def recommend_outfits(model, users_int_id, outfit_entity_ids_to_predict, user_features_lightfm, item_features_lightfm):
    not_yet_liked_outfit_entity_ids = list(outfit_entity_ids_to_predict['entity_int_id'])
    scores = model.predict(users_int_id,
                           not_yet_liked_outfit_entity_ids,
                           item_features=item_features_lightfm,
                           user_features=user_features_lightfm)
    
    recommended_outfits = outfit_entity_ids_to_predict.copy()
    recommended_outfits['scores'] = scores
    recommended_outfits = recommended_outfits.sort_values(by='scores', ascending=False)

    return recommended_outfits



def sql_to_pandas_df(sql: str, vals: list = []):
    conn_string = utils.get_conn_string(constants.DB_CREDS, dbtype="postgres", delim=" ")
    conn = psycopg2.connect(conn_string)
    df = pd.read_sql_query(sql, conn, params=vals)
    conn.close()
    return df


def create_user_features(df_liked_entity, df_entity_merged_with_outfits_and_products, df_users, user_feature_names_with_weights: dict, specify_user_weights: bool=True, users_int_id: int=None):
    
    df_liked_entity_merged = df_liked_entity.merge(df_users,
                                                   how='inner',
                                                   on='user_id')
    
    if users_int_id:
        _df_liked_entity_merged = df_liked_entity_merged.loc[df_liked_entity_merged['users_int_id'] == users_int_id]
    else:
        _df_liked_entity_merged = df_liked_entity_merged
    
    
    df_liked_entity_merged = _df_liked_entity_merged.merge(df_entity_merged_with_outfits_and_products,
                                                           how='inner',
                                                           on='entity_id')

    # Create user features
    user_features = df_liked_entity_merged.groupby(['user_id']).apply(create_features__users,
                                                                      user_feature_names_with_weights,
                                                                      specify_user_weights=specify_user_weights)

    # print(user_features)
    df_users_with_features = df_users.merge(user_features,
                                            how='outer',
                                            on='user_id')

    df_users_with_features = df_users_with_features.dropna()

    # print(df_users)
    df_users_with_features['features_with_int_id'] = generate_feature_with_int_id(df_users_with_features,
                                                                                  'users_int_id',
                                                                                  features_col='features_without_weights')
    return df_users_with_features


def create_features__users(df, cols_with_weights: dict={}, specify_user_weights: bool=False) -> pd.Series:
    if specify_user_weights:
        all_features_df = df.apply(create_features,
                                   axis=1,
                                   args=(cols_with_weights, True))

        # We need to flatten out the features
        features_with_weights = list(itertools.chain(*all_features_df['features_with_weights']))
        features_without_weights = list(itertools.chain(*all_features_df['features_without_weights']))
    else:
        features_with_weights = features__count_and_sum(df)
        features_without_weights = list(set(df['features_without_weights'].sum()))

    series_dict = {
        "features_with_weights": features_with_weights,
        "features_without_weights": features_without_weights
    }
    return pd.Series(series_dict, index=['features_with_weights', 'features_without_weights'])


def create_features(series, cols_with_weights, skip_nulls: bool=False):
    features_with_weights = []
    features_without_weights = []
#     print(series)
    for col_name, val in series.iteritems():
        if col_name in cols_with_weights:
            if skip_nulls and pd.isnull(val):
                continue
            feature_name = col_name + ":" + str(val)
            feature_weight = cols_with_weights[col_name]['weight']
            features_with_weights.append({feature_name: feature_weight})
            features_without_weights.append(feature_name)

    series_dict = {
        "features_with_weights": features_with_weights,
        "features_without_weights": features_without_weights
    }
    return pd.Series(series_dict, index=['features_with_weights', 'features_without_weights'])


def generate_feature_with_int_id(df, id_col_name, features_col="features_without_weights"):
    """
    Generate features that will be ready for feeding into lightfm

    Parameters
    ----------
    dataframe: Dataframe
        Pandas Dataframe which contains features
    features_name : List
        List of feature columns name avaiable in dataframe
    id_col_name: String
        Column name which contains id of the question or
        answer that the features will map to.
        There are two possible values for this variable.
        1. questions_id_num
        2. professionals_id_num

    Returns
    -------
    Pandas Series
        A pandas series containing process features
        that are ready for feed into lightfm.
        The format of each value
        will be (user_id, ['feature_1', 'feature_2', 'feature_3'])
        Ex. -> (1, ['military', 'army', '5'])
    """
    features = df[features_col]
    features = list(zip(df[id_col_name], features))
    return features

