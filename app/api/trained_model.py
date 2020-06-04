import pickle
import psycopg2 as pg
import toolz

from api import constants


def get_trained_model() -> dict:
    sql = """
        SELECT * FROM public.trained_recommendation_models
        WHERE model_version = 0.1
    """
    # conn_string = utils.get_conn_string(constants.DB_CREDS, dbtype="postgres", delim=" ")
    with pg.connect(**constants.DB_CREDS) as conn, conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(sql)
        columns = [column[0] for column in cur.description]
        row = cur.fetchone()
        if row is None:
            return {}
        d_row = dict(zip(columns, row))

    # Convert specified fields to bytes
    data_bytes = toolz.thread_first(d_row,
                                    (toolz.update_in, ['model_version'], float),
                                    (toolz.update_in, ['model_pickle'], bytes),
                                    (toolz.update_in, ['user_features_pickle'], bytes),
                                    (toolz.update_in, ['item_features_pickle'], bytes),
                                    (toolz.update_in, ['dataset_pickle'], bytes),)

    # Unpickle specified fields
    model_data = toolz.thread_first(data_bytes,
                                    (toolz.update_in, ['model_pickle'], pickle.loads),
                                    (toolz.update_in, ['user_features_pickle'], pickle.loads),
                                    (toolz.update_in, ['item_features_pickle'], pickle.loads),
                                    (toolz.update_in, ['dataset_pickle'], pickle.loads),)

    # Return model data without specified fields
    return model_data


model_info = get_trained_model()
