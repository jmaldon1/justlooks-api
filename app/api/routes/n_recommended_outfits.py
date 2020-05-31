from api.routes import justlooks_api
from api import trained_model


@justlooks_api.route("/n_recommended_outfits", methods=['GET'])
def n_recommended_outfits():
    # print(trained_model.get_trained_model())
    model_info = trained_model.model_info
    # print(model_info)
    sql = """
        
    """
    # model = trained_model.model
    # user_features_lightfm = trained_model.user_features_lightfm
    # item_features_lightfm = trained_model.item_features_lightfm

    # print(user_features_lightfm)
    return "Hello, World!"