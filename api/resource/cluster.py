# -*- coding: utf-8 -*-
'''/cluster resource'''
import uuid

from flask.ext.restful import Resource
from flask_restful_swagger import swagger

from ..model import GluuCluster
from api.database import db


class Cluster(Resource):
    """
    creats a empty gluu cluster
    cluster object holdes all states
    """
    @swagger.operation(
        notes='Gives cluster info/state',
        nickname='getcluster',
        parameters=[],
        responseMessages=[
            {
              "code": 200,
              "message": "List cluster information",
            },
            {
                "code": 404,
                "message": "Cluster not found",
            },
            {
                "code": 500,
                "message": "Internal Server Error"
            },
        ],
        summary='TODO'
        )
    def get(self, cluster_id=None):
        if cluster_id:
            obj = db.get(cluster_id, GluuCluster)
            if not obj:
                return {"code": 404, "message": "Cluster not found"}, 404
            return obj.as_dict()

        obj_list = db.all(GluuCluster)
        return [item.as_dict() for item in obj_list]

    @swagger.operation(
        notes='Create a new cluster',
        nickname='postcluster',
        parameters=[],
        responseMessages=[
            {
                "code": 201,
                "message": "Created",
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='Create a new cluster and persist json to disk.'
        )
    def post(self):
        c = GluuCluster()
        c.id = "{}".format(uuid.uuid4())
        c.description = "Test Cluster"
        db.persist(c)
        return c.as_dict(), 201

    @swagger.operation(
        notes='delete a cluster',
        nickname='delcluster',
        parameters=[],
        responseMessages=[
            {
                "code": 204,
                "message": "Cluster deleted"
            },
            {
                "code": 500,
                "message": "Internal Server Error",
            },
        ],
        summary='TODO'
        )
    def delete(self, cluster_id):
        db.delete(cluster_id, GluuCluster)
        return {}, 204
