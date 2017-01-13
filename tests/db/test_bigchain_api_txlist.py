"""
Test getting a list of transactions from the backend.

This test module defines it's own fixture which is used by all the tests.
"""
import pytest


@pytest.fixture
def txlist(b, user_pk, user2_pk, user_sk, user2_sk, genesis_block):
    from bigchaindb.models import Transaction
    prev_block_id = genesis_block.id

    # Create first block with CREATE transactions
    create1 = Transaction.create([user_pk], [([user2_pk], 6)]) \
        .sign([user_sk])
    create2 = Transaction.create([user2_pk],
                                 [([user2_pk], 5), ([user_pk], 5)]) \
                         .sign([user2_sk])
    block1 = b.create_block([create1, create2])
    b.write_block(block1)

    transfer1 = Transaction.transfer(create1.to_inputs(),
                                     [([user_pk], 8)],
                                     create1.id).sign([user2_sk])
    block2 = b.create_block([transfer1])
    b.write_block(block2)

    prev_block_id = genesis_block.id
    for bid in [block1.id, block2.id]:
        vote = b.vote(bid, prev_block_id, True)
        prev_block_id = bid
        b.write_vote(vote)

    return type('', (), {
        'user1': user_pk,
        'user2': user2_pk,
        'create1': create1.id,
        'create2': create2.id,
        'transfer1': transfer1.id,
        'block1': block1.id,
        'block2': block2.id,
    })


@pytest.mark.bdb
def test_get_txlist_by_asset(b, txlist):
    from bigchaindb.backend import query
    res = query.get_transactions_list(
        b.connection,
        asset_id=txlist.create1)
    assert set(res) == set([txlist.transfer1])  # , create1]) - should be there


@pytest.mark.bdb
def test_get_txlist_by_operation(b, txlist):
    from bigchaindb.backend import query
    res = query.get_transactions_list(
        b.connection,
        operation='CREATE')
    assert set(res) == set([txlist.create1, txlist.create2])
