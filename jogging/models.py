import datetime

import logging as py_logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

class LogSummary(models.Model):
    "A summary of the log messages"
    level = models.CharField(max_length=128)
    source = models.CharField(max_length=128, blank=True)
    host = models.CharField(max_length=200, blank=True, null=True)
    earliest = models.DateTimeField(default=datetime.datetime.now)
    latest = models.DateTimeField(default=datetime.datetime.now)
    hits = models.IntegerField(default=0, null=False)
    msg = models.TextField()

    class Meta:
        unique_together = ('level', 'source', 'host')
        verbose_name = 'Log Summary'
        verbose_name_plural = 'Log Summaries'

    def abbrev_msg(self, maxlen=500):
        if len(self.msg) > maxlen:
            return u'%s ...' % self.msg[:maxlen]
        return self.msg
    abbrev_msg.short_description = u'Most recent msg'

    def __unicode__(self):
        return u"<SUMMARY %s: %s %s %s>" % (self.level, self.host, self.source, self.abbrev_msg(maxlen=20))

class Log(models.Model):
    "A log message, used by jogging's DatabaseHandler"
    datetime = models.DateTimeField(default=datetime.datetime.now)
    level = models.CharField(max_length=128)
    msg = models.TextField()
    source = models.CharField(max_length=128, blank=True)
    host = models.CharField(max_length=200, blank=True, null=True)
    summary = models.ForeignKey(LogSummary, related_name='logs', blank=True, null=True)

    class Meta:
        pass

    def abbrev_msg(self, maxlen=500):
        if len(self.msg) > maxlen:
            return u'%s ...' % self.msg[:maxlen]
        return self.msg
    abbrev_msg.short_description = u'abbreviated msg'

    def __unicode__(self):
        return u"<%s: %s %s %s>" % (self.level, self.host, self.source, self.abbrev_msg(maxlen=20))

## Signals

def summary_deleted_callback(sender, **kwargs):
    "When summary deleted, delete matching child logs"
    summary = kwargs['instance']
    Log.objects.filter(level=summary.level,
                       source=summary.source,
                       host=summary.host).delete()
    return

def log_saved_callback(sender, **kwargs):
    "When a log is saved, add it to the summary"
    log = kwargs['instance']
    created = kwargs['created']
    if created:
        (summary, summary_created) = LogSummary.objects.get_or_create(level = log.level,
                                                                      source = log.source,
                                                                      host = log.host,
                                                                      defaults = {'earliest' : log.datetime})
        summary.latest = log.datetime
        summary.msg = log.msg
        summary.hits += 1
        summary.save()
        log.summary = summary
        log.save()

    return

models.signals.pre_delete.connect(summary_deleted_callback, sender=LogSummary)
models.signals.post_save.connect(log_saved_callback, sender=Log)

## Set up logging handlers

def jogging_init():
    def add_handlers(logger, handlers):
        if not handlers:
            return

        for handler in handlers:
            if type(handler) is dict:
                if 'format' in handler:
                    handler['handler'].setFormatter(py_logging.Formatter(handler['format']))
                if 'level' in handler:
                    handler['handler'].setLevel(handler['level'])
                logger.addHandler(handler['handler'])
            else:
                logger.addHandler(handler)


    if hasattr(settings, 'LOGGING'):
        for module, properties in settings.LOGGING.items():
            logger = py_logging.getLogger(module)

            if 'level' in properties:
                logger.setLevel(properties['level'])
            elif hasattr(settings, 'GLOBAL_LOG_LEVEL'):
                logger.setLevel(settings.GLOBAL_LOG_LEVEL)
            elif 'handlers' in properties:
                # set the effective log level of this loger to the lowest so
                # that logging decisions will always be passed to the handlers
                logger.setLevel(1)
                pass
            else:
                raise ImproperlyConfigured(
                    "A logger in settings.LOGGING doesn't have its log level set. " +
                    "Either set a level on that logger, or set GLOBAL_LOG_LEVEL.")

            handlers = []
            if 'handler' in properties:
                handlers = [properties['handler']]
            elif 'handlers' in properties:
                handlers = properties['handlers']
            elif hasattr(settings, 'GLOBAL_LOG_HANDLERS'):
                handlers = settings.GLOBAL_LOG_HANDLERS

            add_handlers(logger, handlers)

    elif hasattr(settings, 'GLOBAL_LOG_HANDLERS'):
        logger = py_logging.getLogger('')
        if settings.get('DEBUG', False):
            default_level = logging.WARNING
        else:
            default_level = logging.DEBUG
        default_level = settings.get('GLOBAL_LOG_LEVEL', default_level)
        logger.setLevel(default_level)
        handlers = settings.GLOBAL_LOG_HANDLERS

        add_handlers(logger, handlers)

jogging_init()
