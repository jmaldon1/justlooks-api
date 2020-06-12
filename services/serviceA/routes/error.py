from services.serviceA.routes import serviceA_api


@serviceA_api.errorhandler(404)
def handle_404(error):
    """
    This is returned if an undefined route is called
    """
    return make_response(jsonify({'error': 'Not found'}), 404)