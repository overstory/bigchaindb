from pytest import raises

from bigchaindb.common.exceptions import SchemaValidationError
from bigchaindb.common.schema import validate_transaction_schema


def test_validate_transaction_create(create_tx):
    validate_transaction_schema(create_tx.to_dict())


def test_validate_transaction_signed_create(signed_create_tx):
    import json, time
    from bigchaindb.common.utils import serialize
    from bigchaindb.common.transaction import Transaction
    payload = serialize(signed_create_tx.to_dict())
    t = time.time()
    for i in range(1000):
        obj = json.loads(payload)
        validate_transaction_schema(obj)
        tx = Transaction.from_dict(obj)
    print("%.3f", time.time() - t)
    validate_transaction_schema(signed_create_tx.to_dict())


def test_validate_transaction_signed_transfer(signed_transfer_tx):
    validate_transaction_schema(signed_transfer_tx.to_dict())


def test_validate_transaction_fails():
    with raises(SchemaValidationError):
        validate_transaction_schema({})


def test_validate_fails_metadata_empty_dict(create_tx):
    create_tx.metadata = {'a': 1}
    validate_transaction_schema(create_tx.to_dict())
    create_tx.metadata = None
    validate_transaction_schema(create_tx.to_dict())
    create_tx.metadata = {}
    with raises(SchemaValidationError):
        validate_transaction_schema(create_tx.to_dict())
