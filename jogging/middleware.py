class LoggingMiddleware(object):

    def process_exception(self, request, exception):
        from jogging import logging
        try:
            logging.exception(exception=exception, request=request)
        except StandardException, e:
            import sys
            print >>sys.stdout, "ERROR: Exception occured while logging an exception: %s", repr(e)
