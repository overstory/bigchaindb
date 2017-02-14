import time
import logging

import marklogic as ml

from bigchaindb.backend.connection import Connection

logger = logging.getLogger(__name__)

# ToDo: This is the beginning of a port to MarkLogic as the backend
# There are two options here:
#   1) Depend on the ML REST API, translate the various calls in the "query.py" interface
#      to calls to via that API, which might entail some eval calls of XQuery code.  This is
#      make not be very efficient, but would require only some minor configuration, not any
#      custom code on MarkLogic.
#   2) Write a bespoke REST API with endpoints to implement the various calls needed for the
#      "query.py" interface.  This is the preferred solution but would require the XQuery code
#      to be installed on MarkLogic, and making sure the versions match.  It would yield the best
#      efficiency and reduce coupling by isolating the XQuery from the Python code.



class MarkLogicDBConnection(Connection):
    """
    This class is a proxy to run queries against the database, it is:

        - lazy, since it creates a connection only when needed
        - resilient, because before raising exceptions it tries
          more times to run the query or open a connection.
    """

    def __init__(self, host, port, dbname, max_tries=3):
        """Create a new :class:`~.MarkLogicDBConnection` instance.

        See :meth:`.Connection.__init__` for
        :attr:`host`, :attr:`port`, and :attr:`dbname`.

        Args:
            max_tries (int, optional): how many tries before giving up.
                Defaults to 3.
        """

        self.host = host
        self.port = port
        self.dbname = dbname
        self.max_tries = max_tries
        self.conn = None

    def run(self, query):
        """Run a MarkLogic query.

        Args:
            query: the RethinkDB query.

        Raises:
            :exc:`rethinkdb.ReqlDriverError`: After
                :attr:`~.RethinkDBConnection.max_tries`.
        """

        if self.conn is None:
            self._connect()

        for i in range(self.max_tries):
            try:
                return query.run(self.conn)
            except ml.ReqlDriverError:
                if i + 1 == self.max_tries:
                    raise
                self._connect()

    def _connect(self):
        """Set a connection to RethinkDB.

        The connection is available via :attr:`~.MarkLogicDBConnection.conn`.

        Raises:
            :exc:`rethinkdb.ReqlDriverError`: After
                :attr:`~.MarkLogicDBConnection.max_tries`.
        """

        for i in range (1, self.max_tries + 1):
            logging.debug('Connecting to database %s:%s/%s. (Attempt %s/%s)',
                          self.host, self.port, self.dbname, i, self.max_tries)
            try:
                self.conn = ml.connect (host=self.host, port=self.port, db=self.dbname)
            except ml.ReqlDriverError:
                if i == self.max_tries:
                    raise
                wait_time = 2**i
                logging.debug('Error connecting to database, waiting %ss', wait_time)
                time.sleep(wait_time)
