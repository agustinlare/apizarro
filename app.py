from werkzeug.datastructures import FileStorage
from flask import Flask, url_for, send_file
from flask_restplus import Api, Resource
from flask_oidc import OpenIDConnect
from flask_cors import CORS
from get_config import get_config, assert_this
from ocp_fx import *
import logging
import os
import time

logging.basicConfig(format='%(asctime)pips|%(levelname)s|%(message)s', level=logging.ERROR)
logging.captureWarnings(True)

api = Flask(__name__)
SECRET_KEY = os.urandom(32)

if os.getenv('FLASK_APP'):
    @property
    def specs_url(self):
        return url_for(self.endpoint('specs'), _external=True, _scheme='https')    
    Api.specs_url = specs_url

CORS(api, supports_credentials=True, resources={r"*": {"origins": "*"}})
zarro = Api(app=api, 
			version="1.5", 
			title="PAAS Self-service API, (APIzarro)", 
			description="by Coffe Table PAAS Team - SANTEC ARG", 
			security='Bearer Auth')

api.config.update(
	{
		'SECRET_KEY': 'SomethingNotEntirelySecret',
		'TESTING': True,
		'DEBUG': True,
		'OIDC_CLIENT_SECRETS': 'conf/oidc_client_secrets.json',
		'OIDC_ID_TOKEN_COOKIE_SECURE': False,
		'OIDC_REQUIRE_VERIFIED_EMAIL': False,
		'OIDC_USER_INFO_ENABLED': True,
		'OIDC_OPENID_REALM': 'farmasalud',
		'OIDC_SCOPES': ['openid', 'email', 'profile'],
		'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
	}
)

oidc = OpenIDConnect(api)

projects = zarro.namespace('projects', description="Project == OKD_PROJECT == Namespace")
# @projects.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@projects.route('/<cluster>')
class get_project(Resource):
    # @oidc.accept_token(require_token=True)
    def get(self, cluster):
        try:
            resp = get_project_list(cluster)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Failed to fetch " + cluster )
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

project_del_model = projects.parser()
project_del_model.add_argument('name')
# @projects.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@projects.route('/<ambiente>/<project>')
class delete_project(Resource):
    # @oidc.accept_token(require_token=True)
    def delete(self, ambiente, project):
        try:   
            assert_this(ambiente, project)
            resp = delete_project_ambiente(ambiente, project)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Failed to fetch " + ambiente )
        except AssertionError as e:
            zarro.abort(403, e.__doc__, status = "Forbidden: Unable to perform this action through this API. This incident will be reported", statusCode = "403")
        except Exception as e:
            zarro.abort(400, e.reason, status = "Failed to fetch " + ambiente, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp}

# Pods
pods = zarro.namespace('pods', description="Liste o borre pods segun su nombre o label por cluster o ambiente")
# @pods.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@pods.route('/<cluster>/<project>')
class get_pods_cluster(Resource):
    def get(self, cluster, project):
        try:
            resp = get_pods_list(cluster, project)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Failed to fetch " + cluster + " " + project )
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# @pods.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@pods.route('/<env>/<project>/label/<label>')
class pods_label(Resource):
    # @oidc.accept_token(require_token=True)
    def get(self, env, project, label):
        try:
            if env in get_config().keys():
                resp = get_pods_label_cluster(env, project, label)
            else:
                resp = get_pods_label_ambiente(env, project, label)

        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

    def delete(self, env, project, label):
        # @oidc.accept_token(require_token=True)
        try:
            if env in get_config().keys():
                resp = delete_pods_label_cluster(env, project, label)
            else:
                resp = delete_pods_label_ambiente(env, project, label)

        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# @pods.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@pods.route('/<cluster>/<project>/name/<name>')
class delete_pods_x_name(Resource):
    # @oidc.accept_token(require_token=True)
    def delete(self, cluster, project, name):
        try:
            resp = delete_pods_name(cluster, project, name)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# Elastic
es = zarro.namespace('elasticsearch', description="Workaround para issue de duplicacion de Index en Elasticsearch de Kibana")
# @es.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@es.route('/<ambiente>/index/<user>')
class put_userindex(Resource):
    # @oidc.accept_token(require_token=True)
    def put(self, ambiente, user):
        try:
            resp = put_user_index(ambiente, user)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except AssertionError as e:
            zarro.abort(404, e.args[0], status = e.__doc__, statusCode = "404")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp}

# Cronjobs
cronjobs = zarro.namespace('cronjobs', description="Elimine o deshabilite cronjobs")
# @cronjobs.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@cronjobs.route('/<env>/<project>/<name>')
class delete_cj_cluster(Resource):
    # @oidc.accept_token(require_token=True)
    def delete(self, env, project, name):
        try: 
            if env in get_config().keys():
                resp = delete_cronjob_cluster(env, project, name)
            else:
                resp = delete_cronjob_ambiente(env, project, name)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# @cronjobs.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@cronjobs.route('/<env>/<project>/<name>/enable')
class cj_enable(Resource):
    # @oidc.accept_token(require_token=True)
    def put(self, env, project, name):
        try:
            if env in get_config().keys():
                resp = toggle_cronjob_cluster(env, project, name, "enable")
            else:
                resp = toggle_cronjob_ambiente(env, project, name, "enable")
        
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:

            return { "status": "OK", "statusCode": 200, "message": resp }

# @cronjobs.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@cronjobs.route('/<env>/<project>/<name>/disable')
class cj_disable(Resource):
    # @oidc.accept_token(require_token=True)
    def put(self, env, project, name):
        try:
            if env in get_config().keys():
                resp = toggle_cronjob_cluster(env, project, name, "disable")
            else:
                resp = toggle_cronjob_ambiente(env, project, name, "disable")
        
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# HPA
hpa = zarro.namespace('hpa', description="Liste, modifique HorizontalPodsAutoscaler resources en ambientes bajo y tambien elimine en todos los ambientes si esta teniendo problemas de estabilidad")
# @hpa.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@hpa.route('/<env>/<project>')
class hpa_get(Resource):
    # @oidc.accept_token(require_token=True)
    def get(self, env, project):
        try:
            if env in get_config().keys():
                resp = get_hpa_cluster(env, project)
            else:
                resp = get_hpa_ambiente(env, project)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# @hpa.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@hpa.route('/<env>/<project>/<name>')
class hpa_delete(Resource):
    # @oidc.accept_token(require_token=True)
    def delete(self, env, project, name):
        try:
            if env in get_config().keys():
                resp = delete_hpa_cluster(env, project, name)
            else:
                resp = delete_hpa_ambiente(env, project, name)
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

hpa_body = hpa.parser()
hpa_body.add_argument('metrics', location='files', type=FileStorage, required=True)
# @hpa.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@hpa.expect(hpa_body)
@hpa.route('/<env>/<project>/testing-metrics/<name>/')
class hpa_editmetrics(Resource):
    # @oidc.accept_token(require_token=True)
    def post(self, env, project, name):
        try:
            assert_this(env)
            args = hpa_body.parse_args()

            if env in get_config().keys():
                resp = edit_hpa_cluster(env, project, name, args['metrics'])
            else:
                resp = edit_hpa_ambiente(env, project, name, args['metrics'])
        except KeyError as e:
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = e.reason, statusCode = e.status)
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# Experimnetal
# @exp.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
exp = zarro.namespace('experimental', description="Funciones experimentales")
@exp.route('/<cluster>/<project>/<pods>/<container>/logs')
class get_logs(Resource):
    # @oidc.accept_token(require_token=True)
    def get(self, cluster, project, pod, container):
        try:
            resp = get_logs_legacy(cluster,project,pod,container)
            
            t = time.localtime()
            filename = "logs/" + pod + time.strftime("%Y%m%d%H%M%S", t) + ".log"
            f = open(filename, "w")
            f.write(resp)
            f.close()

        except KeyError as e:   
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return send_file(filename, as_attachment=True)

# @exp.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@exp.route('/<env>/<project>/resourcequota/duplicarquota')
class red_button(Resource):
    # @oidc.accept_token(require_token=True)
    def put(self, env, project):
        try:
            resp = duplicar_quota(env, project)
        except KeyError as e:   
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

# @exp.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@exp.route('/<env>/<project>/<user>')
class rbac_validator(Resource):
    # @oidc.accept_token(require_token=True)
    def get(self, env, project, user):
        if can_you_do_this(env, project, user):
           resp = "Yes"
        else:
           resp = "No, can do"

        return { "status": "OK", "statusCode": 200, "message": resp }

@exp.doc(params={'Authorization': {'in': 'header', 'description': 'An authorization token example : Bearer JWT_TOKEN'}},responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, required=True)
@exp.route('/pruebajwt')
class jwt_validator(Resource):
	@oidc.accept_token(require_token=True)
	def get(self):
		try:
			resp = "JWT Approved"
			return  { "status": "OK", "statusCode": 200, "message": resp }
		except Exception as error:
			return { "status": "FAILED", "statusCode": 500, "message": error.args[0]}

ruta = zarro.namespace('ruta', description='Agregado de ruta corta')
@ruta.route('/<ambiente>/<projecto>/<service>/<nombre>')
class rutacorta(Resource):
    def post(self, ambiente, projecto, service, nombre):
        try:
            resp = new_ruta_corta(ambiente, projecto, service, nombre)
        except KeyError as e:   
            zarro.abort(500, e.__doc__, status = "Could not save information. " + str(e), statusCode = "500")
        except Exception as e:
            zarro.abort(400, e.__doc__, status = "Could not save information. " + str(e), statusCode = "400")
        else:
            return { "status": "OK", "statusCode": 200, "message": resp }

if __name__ == '__main__':
	if os.getenv('FLASK_APP'):
		api.run(host=os.environ['FLASK_RUN_HOST'], port=os.environ['FLASK_RUN_PORT'])
	else:
		api.run(debug=True,port='5001')