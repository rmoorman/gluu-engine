# The MIT License (MIT)
#
# Copyright (c) 2015 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from flask_restful_swagger import swagger
from flask.ext.restful import fields

from .base import BaseModel


@swagger.model
class oxauthNode(BaseModel):
    # Swager Doc
    resource_fields = {
        "id": fields.String(attribute="Node unique identifier"),
        "name": fields.String(attribute="Node name"),
        "type": fields.String(attribute="Node type"),
        "cluster_id": fields.String(attribute="Cluster ID"),
    }

    def __init__(self):
        self.id = ""
        self.cluster_id = ""
        self.name = ""
        self.type = "oxauth"

        self.oxauth_lib = "/opt/tomcat/webapps/oxauth/WEB-INF/lib"
        self.oxauth_client_id = ""
        self.oxauth_client_pw = ""
        self.oxauth_client_encoded_pw = ""
        self.oxauth_error_json = "api/templates/salt/oxauth/oxauth-errors.json"
        self.oxauth_ldap_properties = "/opt/tomcat/conf/oxauth-ldap.properties"
        self.oxauth_config_xml = "/opt/tomcat/conf/oxauth-config.xml"
        self.tomcat_oxauth_static_conf_json = "/opt/tomcat/conf/oxauth-static-conf.json"
