from sc4_mapper import helpers


def test_dlg_stub():
    stub = helpers.DlgStub()
    # Ensure it doesn't crash
    stub.Update(1, 1)


def test_cached_listdir(tmp_path):
    # Create some files
    d = tmp_path / "test_dir"
    d.mkdir()
    f = d / "file.txt"
    f.write_text("hello")

    path = str(d)

    # First call - should cache
    res1 = helpers.cached_listdir(path)
    assert "file.txt" in res1

    # Modify dir outside cache
    f2 = d / "file2.txt"
    f2.write_text("world")

    # Second call - should return cached value (without file2.txt)
    res2 = helpers.cached_listdir(path)
    assert "file2.txt" not in res2
    assert res1 == res2

    # Clear cache and check again
    helpers.global_cache.clear()
    res3 = helpers.cached_listdir(path)
    assert "file2.txt" in res3
