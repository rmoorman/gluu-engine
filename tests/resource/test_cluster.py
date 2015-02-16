import json
import os
import uuid


def test_cluster_post(app, config):
    from api.model import GluuCluster

    resp = app.test_client().post("/cluster")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 201
    for field in GluuCluster.resource_fields.keys():
        assert field in actual_data

    # remove test file
    os.unlink("{}/cluster_{}.json".format(config.DB, actual_data["id"]))


def test_cluster_get(app, config):
    from api.model import GluuCluster

    cluster = GluuCluster()
    cluster.id = "{}".format(uuid.uuid4())
    data = cluster.persist(config.DB)

    resp = app.test_client().get("/cluster/{}".format(data.id))
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert data.as_dict() == actual_data
    for field in cluster.resource_fields.keys():
        assert field in actual_data

    # remove test file
    os.unlink("{}/cluster_{}.json".format(config.DB, data.id))


def test_cluster_get_invalid_id(app, config):
    resp = app.test_client().get("/cluster/random-invalid-id")
    actual_data = json.loads(resp.data)
    assert resp.status_code == 404
    assert actual_data["code"] == 404
    assert "message" in actual_data


def test_cluster_get_list(app, config):
    from api.model import GluuCluster

    cluster = GluuCluster()
    cluster.id = "{}".format(uuid.uuid4())
    data = cluster.persist(config.DB)

    resp = app.test_client().get("/cluster")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 1

    fields = cluster.resource_fields.keys()
    for item in actual_data:
        for field in fields:
            assert field in item

    # remove test file
    os.unlink("{}/cluster_{}.json".format(config.DB, data.id))


def test_cluster_get_list_empty(app, config):
    resp = app.test_client().get("/cluster")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert len(actual_data) == 0
    assert actual_data == []


def test_cluster_delete(app, config):
    from api.model import GluuCluster

    cluster = GluuCluster()
    cluster.id = "{}".format(uuid.uuid4())
    data = cluster.persist(config.DB)

    resp = app.test_client().delete("/cluster/{}".format(data.id))
    actual_data = json.loads(resp.data)

    assert resp.status_code == 200
    assert actual_data["code"] == 200
    assert actual_data["message"] == "Cluster deleted"


def test_cluster_delete_failed(app, config):
    resp = app.test_client().delete("/cluster/random-invalid-id")
    actual_data = json.loads(resp.data)

    assert resp.status_code == 404
    assert actual_data["code"] == 404