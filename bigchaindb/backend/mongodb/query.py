"""Query implementation for MongoDB"""

from time import time

from pymongo import ReturnDocument
from pymongo import errors

from bigchaindb import backend
from bigchaindb.common.exceptions import CyclicBlockchainError
from bigchaindb.backend.utils import module_dispatch_registrar
from bigchaindb.backend.mongodb.connection import MongoDBConnection


register_query = module_dispatch_registrar(backend.query)


@register_query(MongoDBConnection)
def write_transaction(conn, signed_transaction):
    try:
        return conn.db['backlog'].insert_one(signed_transaction)
    except errors.DuplicateKeyError:
        return


@register_query(MongoDBConnection)
def update_transaction(conn, transaction_id, doc):
    # with mongodb we need to add update operators to the doc
    doc = {'$set': doc}
    return conn.db['backlog']\
               .find_one_and_update({'id': transaction_id},
                                    doc,
                                    return_document=ReturnDocument.AFTER)


@register_query(MongoDBConnection)
def delete_transaction(conn, *transaction_id):
    return conn.db['backlog'].delete_many({'id': {'$in': transaction_id}})


@register_query(MongoDBConnection)
def get_stale_transactions(conn, reassign_delay):
    return conn.db['backlog']\
            .find({'assignment_timestamp': {'$lt': time() - reassign_delay}},
                  projection={'_id': False})


@register_query(MongoDBConnection)
def get_transaction_from_block(conn, transaction_id, block_id):
    try:
        return conn.db['bigchain'].aggregate([
            {'$match': {'id': block_id}},
            {'$project': {
                'block.transactions': {
                    '$filter': {
                        'input': '$block.transactions',
                        'as': 'transaction',
                        'cond': {
                            '$eq': ['$$transaction.id', transaction_id]
                        }
                    }
                }
            }}]).next()['block']['transactions'].pop()
    except (StopIteration, IndexError):
        # StopIteration is raised if the block was not found
        # IndexError is returned if the block is found but no transactions
        # match
        return


@register_query(MongoDBConnection)
def get_transaction_from_backlog(conn, transaction_id):
    return conn.db['backlog']\
               .find_one({'id': transaction_id},
                         projection={'_id': False, 'assignee': False,
                                     'assignment_timestamp': False})


@register_query(MongoDBConnection)
def get_blocks_status_from_transaction(conn, transaction_id):
    return conn.db['bigchain']\
            .find({'block.transactions.id': transaction_id},
                  projection=['id', 'block.voters'])


@register_query(MongoDBConnection)
def get_txids_by_asset_id(conn, asset_id):
    cursor = conn.db['bigchain'].aggregate([
        {'$match': {
            'block.transactions.asset.id': asset_id
        }},
        {'$unwind': '$block.transactions'},
        {'$match': {
            'block.transactions.asset.id': asset_id
        }},
        {'$project': {'block.transactions.id': True}}
    ])
    return (elem['block']['transactions']['id'] for elem in cursor)


@register_query(MongoDBConnection)
def get_asset_by_id(conn, asset_id):
    cursor = conn.db['bigchain'].aggregate([
        {'$match': {
            'block.transactions.id': asset_id,
            'block.transactions.operation': 'CREATE'
        }},
        {'$unwind': '$block.transactions'},
        {'$match': {
            'block.transactions.id': asset_id,
            'block.transactions.operation': 'CREATE'
        }},
        {'$project': {'block.transactions.asset': True}}
    ])
    # we need to access some nested fields before returning so lets use a
    # generator to avoid having to read all records on the cursor at this point
    return (elem['block']['transactions'] for elem in cursor)


@register_query(MongoDBConnection)
def get_spent(conn, transaction_id, output):
    cursor = conn.db['bigchain'].aggregate([
        {'$unwind': '$block.transactions'},
        {'$match': {
            'block.transactions.inputs.fulfills.txid': transaction_id,
            'block.transactions.inputs.fulfills.output': output
        }}
    ])
    # we need to access some nested fields before returning so lets use a
    # generator to avoid having to read all records on the cursor at this point
    return (elem['block']['transactions'] for elem in cursor)


@register_query(MongoDBConnection)
def get_owned_ids(conn, owner):
    cursor = conn.db['bigchain'].aggregate([
        {'$unwind': '$block.transactions'},
        {'$match': {
            'block.transactions.outputs.public_keys': {
                '$elemMatch': {'$eq': owner}
            }
        }}
    ])
    # we need to access some nested fields before returning so lets use a
    # generator to avoid having to read all records on the cursor at this point
    return (elem['block']['transactions'] for elem in cursor)


@register_query(MongoDBConnection)
def get_votes_by_block_id(conn, block_id):
    return conn.db['votes']\
            .find({'vote.voting_for_block': block_id},
                  projection={'_id': False})


@register_query(MongoDBConnection)
def get_votes_by_block_id_and_voter(conn, block_id, node_pubkey):
    return conn.db['votes']\
            .find({'vote.voting_for_block': block_id,
                   'node_pubkey': node_pubkey},
                  projection={'_id': False})


@register_query(MongoDBConnection)
def write_block(conn, block):
    return conn.db['bigchain'].insert_one(block.to_dict())


@register_query(MongoDBConnection)
def get_block(conn, block_id):
    return conn.db['bigchain'].find_one({'id': block_id},
                                        projection={'_id': False})


@register_query(MongoDBConnection)
def has_transaction(conn, transaction_id):
    return bool(conn.db['bigchain']
                .find_one({'block.transactions.id': transaction_id}))


@register_query(MongoDBConnection)
def count_blocks(conn):
    return conn.db['bigchain'].count()


@register_query(MongoDBConnection)
def count_backlog(conn):
    return conn.db['backlog'].count()


@register_query(MongoDBConnection)
def write_vote(conn, vote):
    return conn.db['votes'].insert_one(vote)


@register_query(MongoDBConnection)
def get_genesis_block(conn):
    return conn.db['bigchain'].find_one(
        {'block.transactions.0.operation': 'GENESIS'},
        {'_id': False}
    )


@register_query(MongoDBConnection)
def get_last_voted_block(conn, node_pubkey):
    last_voted = conn.db['votes']\
                  .find({'node_pubkey': node_pubkey},
                        sort=[('vote.timestamp', -1)])

    # pymongo seems to return a cursor even if there are no results
    # so we actually need to check the count
    if last_voted.count() == 0:
        return get_genesis_block(conn)

    mapping = {v['vote']['previous_block']: v['vote']['voting_for_block']
               for v in last_voted}

    last_block_id = list(mapping.values())[0]

    explored = set()

    while True:
        try:
            if last_block_id in explored:
                raise CyclicBlockchainError()
            explored.add(last_block_id)
            last_block_id = mapping[last_block_id]
        except KeyError:
            break

    return get_block(conn, last_block_id)


@register_query(MongoDBConnection)
def get_unvoted_blocks(conn, node_pubkey):
    return conn.db['bigchain'].aggregate([
        {'$lookup': {
            'from': 'votes',
            'localField': 'id',
            'foreignField': 'vote.voting_for_block',
            'as': 'votes'
        }},
        {'$match': {
            'votes.node_pubkey': {'$ne': node_pubkey},
            'block.transactions.operation': {'$ne': 'GENESIS'}
        }},
        {'$project': {
            'votes': False, '_id': False
        }}
    ])


@register_query(MongoDBConnection)
def get_transactions_list(conn, asset_id, operation=None):
    match = {}
    if asset_id:
        # For CREATE: https://github.com/bigchaindb/bigchaindb/issues/1033
        match['block.transactions.asset.id'] = asset_id

    if operation:
        match['block.transactions.operation'] = operation

    cursor = conn.db['bigchain'].aggregate([
        {'$match': match},
        {'$unwind': '$block.transactions'},
        {'$project': {'block.transactions.id': 1}}
    ])
    return (r['block']['transactions']['id'] for r in cursor)
