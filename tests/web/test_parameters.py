import pytest


def test_valid_txid():
    from bigchaindb.web.views.parameters import valid_txid

    valid = ['18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4',
             '18AC3E7343F016890C510E93F935261169D9E3F565436429830FAF0934F4F8E4']
    for h in valid:
        assert valid_txid(h) == h.lower()

    non = ['18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e',
           '18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e45',
           '18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8eg',
           '18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e ',
           '']
    for h in non:
        with pytest.raises(ValueError):
            valid_txid(h)


def test_valid_bool():
    from bigchaindb.web.views.parameters import valid_bool

    assert valid_bool('true') == True
    valid_bool('false') == False

    with pytest.raises(ValueError):
        valid_bool('TRUE')
    with pytest.raises(ValueError):
        valid_bool('FALSE')
    with pytest.raises(ValueError):
        valid_bool('0')
    with pytest.raises(ValueError):
        valid_bool('1')
    with pytest.raises(ValueError):
        valid_bool('yes')
    with pytest.raises(ValueError):
        valid_bool('no')


def test_valid_ed25519():
    from bigchaindb.web.views.parameters import valid_ed25519

    valid = ['123456789abcdefghijkmnopqrstuvwxyz1111111111',
             '123456789ABCDEFGHJKLMNPQRSTUVWXYZ1111111111']
    for h in valid:
        assert valid_ed25519(h) == h

    with pytest.raises(ValueError):
        valid_ed25519('1234556789abcdefghijkmnopqrstuvwxyz1111111')
    with pytest.raises(ValueError):
        valid_ed25519('1234556789abcdefghijkmnopqrstuvwxyz1111111111')
    with pytest.raises(ValueError):
        valid_ed25519('123456789abcdefghijkmnopqrstuvwxyz111111111l')
    with pytest.raises(ValueError):
        valid_ed25519('123456789abcdefghijkmnopqrstuvwxyz111111111I')
    with pytest.raises(ValueError):
        valid_ed25519('1234556789abcdefghijkmnopqrstuvwxyz11111111O')
    with pytest.raises(ValueError):
        valid_ed25519('1234556789abcdefghijkmnopqrstuvwxyz111111110')


def test_valid_operation():
    from bigchaindb.web.views.parameters import valid_operation

    assert valid_operation('CREATE') == 'CREATE'
    assert valid_operation('TRANSFER') == 'TRANSFER'

    with pytest.raises(ValueError):
        valid_operation('create')
    with pytest.raises(ValueError):
        valid_operation('transfer')
    with pytest.raises(ValueError):
        valid_operation('GENESIS')
    with pytest.raises(ValueError):
        valid_operation('blah')
    with pytest.raises(ValueError):
        valid_operation('')
