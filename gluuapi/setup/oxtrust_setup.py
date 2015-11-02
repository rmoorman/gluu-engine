# -*- coding: utf-8 -*-
# Copyright (c) 2015 Gluu
#
# All rights reserved.

import os.path
from glob import iglob

from .oxauth_setup import OxauthSetup


class OxtrustSetup(OxauthSetup):
    def import_httpd_cert(self):
        self.logger.info("importing httpd cert")

        # imports httpd cert into oxtrust cacerts to avoid
        # "peer not authenticated" error
        cert_cmd = "echo -n | openssl s_client -connect {}:443 | " \
                   "sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' " \
                   "> /tmp/ox.cert".format(self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [cert_cmd])
        self.salt.subscribe_event(jid, self.node.id)

        import_cmd = " ".join([
            "keytool -importcert -trustcacerts",
            "-alias '{}'".format(self.cluster.ox_cluster_hostname),
            "-file /tmp/ox.cert",
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [import_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def delete_httpd_cert(self):
        delete_cmd = " ".join([
            "keytool -delete",
            "-alias {}".format(self.cluster.ox_cluster_hostname),
            "-keystore {}".format(self.node.truststore_fn),
            "-storepass changeit -noprompt",
        ])
        self.logger.info("deleting httpd cert")
        self.salt.cmd(self.node.id, "cmd.run", [delete_cmd])

    def add_host_entries(self, httpd):
        # currently we need to add httpd container hostname
        # to prevent "peer not authenticated" raised by oxTrust;
        # TODO: use a real DNS
        self.logger.info("adding HTTPD entry in oxTrust /etc/hosts file")
        # add the entry only if line is not exist in /etc/hosts
        grep_cmd = "grep -q '^{0} {1}$' /etc/hosts " \
                   "|| echo '{0} {1}' >> /etc/hosts" \
                   .format(httpd.weave_ip,
                           self.cluster.ox_cluster_hostname)
        jid = self.salt.cmd_async(self.node.id, "cmd.run", [grep_cmd])
        self.salt.subscribe_event(jid, self.node.id)

    def remove_host_entries(self, httpd):
        # TODO: use a real DNS
        #
        # currently we need to remove httpd container hostname
        # updating ``/etc/hosts`` in-place will raise "resource or device is busy"
        # error, hence we use the following steps instead:
        #
        # 1. copy the original ``/etc/hosts``
        # 2. find-and-replace entries in copied file
        # 3. overwrite the original ``/etc/hosts``
        self.logger.info("removing HTTPD entry in oxTrust /etc/hosts file")
        backup_cmd = "cp /etc/hosts /tmp/hosts"
        sed_cmd = "sed -i 's/{} {}//g' /tmp/hosts && sed -i '/^$/d' /tmp/hosts".format(
            httpd.weave_ip, self.cluster.ox_cluster_hostname
        )
        overwrite_cmd = "cp /tmp/hosts /etc/hosts"
        self.salt.cmd(
            self.node.id,
            ["cmd.run", "cmd.run", "cmd.run"],
            [[backup_cmd], [sed_cmd], [overwrite_cmd]],
        )

    def render_cache_refresh_template(self):
        src = "nodes/oxtrust/oxtrust-cache-refresh.json"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))

        ldap_hosts = [
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ]
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
        }
        self.render_jinja_template(src, dest, ctx)

    def render_log_config_template(self):
        src = "nodes/oxtrust/oxTrustLogRotationConfiguration.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "tomcat_log_folder": self.node.tomcat_log_folder,
        }
        self.render_jinja_template(src, dest, ctx)

    def render_config_template(self):
        src = "nodes/oxtrust/oxtrust-config.json"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ldap_hosts = ",".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "inum_appliance": self.cluster.inum_appliance,
            "inum_org": self.cluster.inum_org,
            "admin_email": self.cluster.admin_email,
            "ox_cluster_hostname": self.cluster.ox_cluster_hostname,
            "shib_jks_fn": self.cluster.shib_jks_fn,
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "inum_org_fn": self.cluster.inum_org_fn,
            "encoded_shib_jks_pw": self.cluster.encoded_shib_jks_pw,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "oxauth_client_id": self.cluster.oxauth_client_id,
            "oxauth_client_encoded_pw": self.cluster.oxauth_client_encoded_pw,
            "truststore_fn": self.node.truststore_fn,
            "ldap_hosts": ldap_hosts,
        }
        self.render_jinja_template(src, dest, ctx)

    def render_ldap_props_template(self):
        src = "nodes/oxtrust/oxtrust-ldap.properties"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))

        ldap_hosts = ",".join([
            "{}:{}".format(ldap.domain_name, ldap.ldaps_port)
            for ldap in self.cluster.get_ldap_objects()
        ])
        ctx = {
            "ldap_binddn": self.node.ldap_binddn,
            "encoded_ox_ldap_pw": self.cluster.encoded_ox_ldap_pw,
            "ldap_hosts": ldap_hosts,
            "inum_appliance": self.cluster.inum_appliance,
        }
        self.render_jinja_template(src, dest, ctx)

    def render_check_ssl_template(self):
        src = self.get_template_path("nodes/oxtrust/check_ssl")
        dest = "/usr/bin/{}".format(os.path.basename(src))
        ctx = {"ox_cluster_hostname": self.cluster.ox_cluster_hostname}
        self.render_template(src, dest, ctx)
        self.salt.cmd(self.node.id, "cmd.run", ["chmod +x {}".format(dest)])

    def setup(self):
        hostname = "localhost"
        self.create_cert_dir()

        # render config templates
        self.render_cache_refresh_template()
        self.render_log_config_template()
        self.render_config_template()

        self.copy_shib_config("idp")
        self.copy_shib_config("idp/schema")
        self.copy_shib_config("idp/ProfileConfiguration")
        self.copy_shib_config("idp/MetadataFilter")
        self.copy_shib_config("sp")

        self.render_ldap_props_template()
        self.render_server_xml_template()
        self.write_salt_file()
        self.render_check_ssl_template()
        self.copy_import_person_properties()

        self.gen_cert("shibIDP", self.cluster.decrypted_admin_pw,
                      "tomcat", "tomcat", hostname)

        # IDP keystore
        self.gen_keystore(
            "shibIDP",
            self.cluster.shib_jks_fn,
            self.cluster.decrypted_admin_pw,
            "{}/shibIDP.key".format(self.node.cert_folder),
            "{}/shibIDP.crt".format(self.node.cert_folder),
            "tomcat",
            "tomcat",
            hostname,
        )

        self.copy_tomcat_index_html()
        self.add_auto_startup_entry()
        self.start_tomcat()
        self.change_cert_access("tomcat", "tomcat")
        return True

    def teardown(self):
        self.after_teardown()

    def render_server_xml_template(self):
        src = "nodes/oxtrust/server.xml"
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        ctx = {
            "weave_ip": self.node.weave_ip,
            "shib_jks_pass": self.cluster.decrypted_admin_pw,
            "shib_jks_fn": self.cluster.shib_jks_fn,
        }
        self.render_jinja_template(src, dest, ctx)

    def copy_tomcat_index_html(self):
        src = self.get_template_path("nodes/oxtrust/index.html")
        dest = "/opt/tomcat/webapps/ROOT/index.html"
        self.salt.copy_file(self.node.id, src, dest)

    def discover_httpd(self):
        self.logger.info("discovering available httpd within same provider")
        try:
            # if we already have httpd node in the same provider,
            # add entry to /etc/hosts and import the cert
            httpd = self.provider.get_node_objects(type_="httpd")[0]
            self.add_host_entries(httpd)
            self.import_httpd_cert()
        except IndexError:
            pass

    def after_setup(self):
        self.discover_httpd()

    def copy_import_person_properties(self):
        src = self.get_template_path("nodes/oxtrust/gluuImportPerson.properties")
        dest = os.path.join(self.node.tomcat_conf_dir, os.path.basename(src))
        self.salt.copy_file(self.node.id, src, dest)

    def copy_shib_config(self, parent_dir):
        """Copy config files located under shibboleth2 directory.
        """
        # create a generator to keep the result of globbing
        files = iglob(self.get_template_path(
            "nodes/oxtrust/shibboleth2/{}/*".format(parent_dir)
        ))

        parent_dest = "/opt/tomcat/conf/shibboleth2/{}".format(parent_dir)
        mkdir_cmd = "mkdir -p {}".format(parent_dest)
        self.salt.cmd(self.node.id, "cmd.run", [mkdir_cmd])

        for src in files:
            if os.path.isdir(src):
                continue
            fn = os.path.basename(src)
            dest = "{}/{}".format(parent_dest, fn)
            self.logger.info("copying {}".format(fn))
            self.salt.copy_file(self.node.id, src, dest)
