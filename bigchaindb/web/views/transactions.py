"""This module provides the blueprint for some basic API endpoints.

For more information please refer to the documentation on ReadTheDocs:
 - https://docs.bigchaindb.com/projects/server/en/latest/drivers-clients/
   http-client-server-api.html
"""
from flask import current_app, request
from flask_restful import Resource, reqparse


from bigchaindb.common.exceptions import (
    AmountError,
    DoubleSpend,
    InvalidHash,
    InvalidSignature,
    SchemaValidationError,
    OperationError,
    TransactionDoesNotExist,
    TransactionOwnerError,
    TransactionNotInValidBlock,
    ValidationError,
)

import bigchaindb
from bigchaindb.models import Transaction
from bigchaindb.web.views.base import make_error
from bigchaindb.web.views import parameters


class TransactionApi(Resource):
    def get(self, tx_id):
        """API endpoint to get details about a transaction.

        Args:
            tx_id (str): the id of the transaction.

        Return:
            A JSON string containing the data about the transaction.
        """
        pool = current_app.config['bigchain_pool']

        with pool() as bigchain:
            tx = bigchain.get_transaction(tx_id)

        if not tx:
            return make_error(404)

        return tx.to_dict()


class TransactionListApi(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('operation', type=parameters.valid_operation)
        parser.add_argument('unspent', type=parameters.valid_ed25519)
        parser.add_argument('asset_id', type=parameters.valid_txid)
        args = parser.parse_args()

        # Require either asset_id or public_key to continue
        if not args.asset_id or args.public_key:
            make_error(400, message="One of asset_id or unspent required")

        with current_app.config['bigchain_pool'] as bigchain:
            return bigchain.list_transactions(**args)

    def post(self):
        """API endpoint to push transactions to the Federation.

        Return:
            A ``dict`` containing the data about the transaction.
        """
        pool = current_app.config['bigchain_pool']
        monitor = current_app.config['monitor']

        # `force` will try to format the body of the POST request even if the
        # `content-type` header is not set to `application/json`
        tx = request.get_json(force=True)

        try:
            tx_obj = Transaction.from_dict(tx)
        except SchemaValidationError as e:
            return make_error(
                400,
                message='Invalid transaction schema: {}'.format(
                    e.__cause__.message)
            )
        except (ValidationError, InvalidSignature) as e:
            return make_error(
                400,
                'Invalid transaction ({}): {}'.format(type(e).__name__, e)
            )

        with pool() as bigchain:
            try:
                bigchain.validate_transaction(tx_obj)
            except (ValueError,
                    OperationError,
                    TransactionDoesNotExist,
                    TransactionOwnerError,
                    DoubleSpend,
                    InvalidHash,
                    InvalidSignature,
                    TransactionNotInValidBlock,
                    AmountError) as e:
                return make_error(
                    400,
                    'Invalid transaction ({}): {}'.format(type(e).__name__, e)
                )
            else:
                rate = bigchaindb.config['statsd']['rate']
                with monitor.timer('write_transaction', rate=rate):
                    bigchain.write_transaction(tx_obj)

        return tx
