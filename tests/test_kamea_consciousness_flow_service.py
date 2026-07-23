from atlas.services import kamea_consciousness_flow_service as service


def test_service_builds_two_profile_confluence(monkeypatch, tmp_path):
    from atlas.kamea.identity_graph import build_kamea_identity_graph
    import json

    for key, name in (("a", "Nikola Tesla"), ("b", "Thomas Edison")):
        profile_dir = tmp_path / key
        profile_dir.mkdir()
        payload = {"profile_key": key, "identity": {"name": name, "full_name": name}}
        payload["kamea"] = build_kamea_identity_graph(payload)
        # Canonical profile export removes non-JSON tuple keys used only by the
        # raw repeated-node diagnostic map.
        (profile_dir / "profile.payload.json").write_text(json.dumps(payload, skipkeys=True), encoding="utf-8")

    monkeypatch.setattr(service, "profile_artifact_path", lambda key, artifact: tmp_path / key / artifact)
    result = service.build_kamea_consciousness_flow_payload("a", "b")
    assert result["success"] is True
    assert result["reports"]["profile_a"]["tributaries"]["tributary_count"] == 21
    assert result["confluence"]["summary"]["planet_count"] == 7
    assert result["warnings"]
