def test_x_dci_team_id_header_filter_view_basic_auth(
    client_admin, user3_id, team2_id, team3_id, client_user3
):
    # user3 don't have access to any products
    assert client_user3.get("/api/v1/teams").data["_meta"]["count"] == 1
    assert client_user3.get("/api/v1/products").data["_meta"]["count"] == 0

    # admin add user3 to the team2
    add_user3_to_team2 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team2_id, user3_id), data={}
    )
    assert add_user3_to_team2.status_code == 201

    # Now user3 see products available to team2
    assert client_user3.get("/api/v1/teams").data["_meta"]["count"] == 2
    assert client_user3.get("/api/v1/products").data["_meta"]["count"] == 1

    # If we scope the view to team3, then user3 lost the view
    assert (
        client_user3.get("/api/v1/products", headers={"X-Dci-Team-Id": team3_id}).data[
            "_meta"
        ]["count"]
        == 0
    )


def test_x_dci_team_id_header_filter_view_sso(
    client_admin, sso_client_user4, team1_id, team2_id, user4_id
):
    # user4 don't have access to any products or teams
    assert sso_client_user4.get("/api/v1/teams").data["_meta"]["count"] == 0
    assert sso_client_user4.get("/api/v1/products").data["_meta"]["count"] == 0

    # admin add user4 to team1 and team2
    add_user4_to_team1 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team1_id, user4_id), data={}
    )
    assert add_user4_to_team1.status_code == 201
    add_user4_to_team2 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team2_id, user4_id), data={}
    )
    assert add_user4_to_team2.status_code == 201

    # Now user4 see products available to team1 and team2
    assert sso_client_user4.get("/api/v1/teams").data["_meta"]["count"] == 2
    assert sso_client_user4.get("/api/v1/products").data["_meta"]["count"] == 2

    # If we scope the view to team1, then user4 keep the view
    assert (
        sso_client_user4.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team1_id}
        ).data["_meta"]["count"]
        == 2
    )
    # If we scope the view to team2, then user4 lost the view
    assert (
        sso_client_user4.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team2_id}
        ).data["_meta"]["count"]
        == 1
    )


def test_nrt_read_only_user_flag_is_also_filtered_with_x_dci_team_id_header(
    client_admin, client_rh_employee, rh_employee_id, team_redhat_id, team3_id
):
    assert client_rh_employee.get("/api/v1/products").data["_meta"]["count"] == 3
    assert (
        client_rh_employee.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team_redhat_id}
        ).data["_meta"]["count"]
        == 3
    )
    add_rh_employee_to_team3 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team3_id, rh_employee_id), data={}
    )
    assert add_rh_employee_to_team3.status_code == 201
    assert (
        client_rh_employee.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team3_id}
        ).data["_meta"]["count"]
        == 0
    )


def test_nrt_epm_flag_is_also_filtered_with_x_dci_team_id_header(
    client_admin, client_epm, epm_id, team_epm_id, team3_id
):
    assert client_epm.get("/api/v1/products").data["_meta"]["count"] == 3
    assert (
        client_epm.get("/api/v1/products", headers={"X-Dci-Team-Id": team_epm_id}).data[
            "_meta"
        ]["count"]
        == 3
    )
    add_epm_to_team3 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team3_id, epm_id), data={}
    )
    assert add_epm_to_team3.status_code == 201
    assert (
        client_epm.get("/api/v1/products", headers={"X-Dci-Team-Id": team3_id}).data[
            "_meta"
        ]["count"]
        == 0
    )


def test_nrt_admin_flag_is_filtering_view_with_x_dci_team_id_header(
    client_admin, team_admin_id, admin_id, team3_id
):
    assert client_admin.get("/api/v1/products").data["_meta"]["count"] == 3
    assert (
        client_admin.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team_admin_id}
        ).data["_meta"]["count"]
        == 3
    )
    add_epm_to_team3 = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team3_id, admin_id), data={}
    )
    assert add_epm_to_team3.status_code == 201
    assert (
        client_admin.get("/api/v1/products", headers={"X-Dci-Team-Id": team3_id}).data[
            "_meta"
        ]["count"]
        == 0
    )


def test_x_dci_team_id_header_with_team_admin_id_raised_unauthorized(
    client_user3, team_admin_id
):
    assert client_user3.get("/api/v1/products").data["_meta"]["count"] == 0
    assert (
        client_user3.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": team_admin_id}
        ).status_code
        == 401
    )


def test_x_dci_team_id_header_not_an_uuid_raised_exception(client_user1):
    assert (
        client_user1.get(
            "/api/v1/products", headers={"X-Dci-Team-Id": "not an uuid"}
        ).status_code
        == 400
    )
