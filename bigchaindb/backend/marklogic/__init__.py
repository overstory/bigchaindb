"""MarkLogic backend implementation.

Contains a MarkLogic-specific implementation of the
:mod:`~bigchaindb.backend.changefeed`, :mod:`~bigchaindb.backend.query`, and
:mod:`~bigchaindb.backend.schema` interfaces.

You can specify BigchainDB to use MarkLogic as its database backend by either
setting ``database.backend`` to ``'marklogic'`` in your configuration file, or
setting the ``BIGCHAINDB_DATABASE_BACKEND`` environment variable to
``'marklogic'``.

If configured to use MarkLogic, BigchainDB will automatically return instances
of :class:`~bigchaindb.backend.rethinkdb.MarkLogicDBConnection` for
:func:`~bigchaindb.backend.connection.connect` and dispatch calls of the
generic backend interfaces to the implementations in this module.
"""

# Register the single dispatched modules on import.
from bigchaindb.backend.rethinkdb import admin, changefeed, schema, query  # noqa

# MarkLogicDBConnection should always be accessed via
# ``bigchaindb.backend.connect()``.
