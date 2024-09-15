import aio_ld2410


def test_module_version():
    assert hasattr(aio_ld2410, '__version__')
    assert hasattr(aio_ld2410, 'version')
    assert aio_ld2410.version == aio_ld2410.__version__
