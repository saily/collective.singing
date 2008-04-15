from zope import interface
from zope import schema
import zope.component.interfaces
from zope.interface.interfaces import IInterface
from zope.interface.common.mapping import IMapping
from zope.annotation.interfaces import IAnnotatable
import z3c.form.interfaces

class ISalt(interface.Interface):
    """A utility that's a salt for use in creating secrets.
    """


class IRequestBasedSecret(interface.Interface):
    """A utility that provides a secret based on the request.
    """
    def __call__(request):
        """Return an ASCII secret.
        """


class IComposerBasedSecret(interface.Interface):
    """An adapter for composer that provides a secret based on the
    user's data used for the composer (see also 'IComposerData').
    """
    
    def secret(data):
        """Return an ASCII secret.

        'data' is a dict that corresponds to the IComposer's schema.
        """


class ISubscription(IAnnotatable):
    """A subscription to a channel.
    """

    channel = schema.Object(
        title=u"The channel that we're subscribed to",
        schema=IInterface, # should be really IChannel
        )

    secret = schema.ASCIILine(
        title=u"The subscriber's secret, ideally unique across channels",
        description=u"""\
        Might be a hash of the subscriber's e-mail and a secret on the
        server in case we're dealing with an anonymous subscription.
        Used for unsubscription or for providing an overview of all of
        a subscriber's subscriptions.
        """,
        )

    composer_data = schema.Dict(title=u"Composer data")
    collector_data = schema.Dict(title=u"Collector data")
    metadata = schema.Dict(title=u"Metadata")

MESSAGE_STATES = [u'new',   # just added
                  u'sent',  # sent successfully
                  u'error', # error while sending
                  u'retry', # error while sending, but retrying
                  ]

class IMessage(interface.Interface):
    """Messages are objects ready for sending.
    """
    payload = schema.Field(
        title=u"The message's payload, e.g. the e-mail message.",
        )

    subscription = schema.Object(
        title=u"Subscription, referenced for bookkeeping purposes only.",
        schema=ISubscription,
        )

    status = schema.Choice(
        title=u"State",
        description=u"IMessageChanged is fired automatically when this is set",
        values=MESSAGE_STATES)

    status_message = schema.Text(
        title=u"Status details",
        required=False)

    status_changed = schema.Datetime(
        title=u"Last time this message changed its status",
        )

class IMessageChanged(zope.lifecycleevent.interfaces.IObjectModifiedEvent):
    """An object event on the message that signals that the status has
    changed.
    """
    old_status = schema.TextLine(title=u"Old status of message")


class IComposer(interface.Interface):
    """Composers will typically provide a user interface that lets you
    modify the look of the message rendered through it.
    """
    
    name = schema.TextLine(
        title=u"The Composer's format, e.g. 'html'",
        )
    

    title = schema.TextLine(
        title=u"The Composer's title, e.g. 'HTML E-Mail'",
        )
    
    schema = schema.Object(
        title=u"A schema instance for use in the subscription form",
        description=u"Values are stored via the IComposerData adapter per "
        "subscriber.",
        schema=IInterface,
        )

    def render(subscription, items=()):
        """Given a subscription and a list of items, I will create an
        IMessage and return it.
        """

    def render_confirmation(subscription):
        """Given a subscription, I will create an IMessage that the
        user has to react to in order to confirm the subscription, and
        return it.
        """

class ISubscriptionLabel(interface.Interface):
    """Marker interface for field on IComposerSchema that labels a
    subscription.
    """

class ISubscriptionKey(interface.Interface):
    """Marker interface for field on IComposerSchema that serves as a
    key for conflicts.

    For subscriptions per e-mail this is the e-mail field.  No
    subscriptions for the same format and same e-mail address will be
    allowed, then.
    """

class ICollector(interface.Interface):
    """Collectors are useful for automatic newsletters.  They are
    responsible for assembling a list of items for publishing.
    """

    title = schema.TextLine(
        title=u"Title",
        )

    optional = schema.Bool(
        title=u"Subscriber optional",
        )

    schema = schema.Object(
        title=u"A schema instance for use in the subscription form",
        description=u"Values are stored via the ICollectorData adapter per "
        "subscriber.",
        required=False,
        schema=IInterface,
        )

    def get_items(cue=None, subscription=None):
        """Return a tuple '(items, cue)' where 'items' is the items
        that'll be fed into the composer, and 'cue' is an object that
        can be passed to this method again.

        If 'cue' is passed, I will only return items that are newer
        than the items that were returned when the cue was retrieved.

        If 'subscription' is given, I will filter according to the
        subscriber's ICollectorData.
        """

class ITemplate(interface.Interface):
    """Templates are useful for generating and presenting newsletters.
    """

    title = schema.TextLine(
        title=u"Title",
        )

class IScheduler(interface.Interface):
    """A scheduler triggers the sending of messages periodically.
    """
    title = schema.TextLine(
        title=u"Title",
        )

    triggered_last = schema.Datetime(
        title=u"Triggered the last time",
        )

    active = schema.Bool(
        title=u"Active",
        )

    def tick(channel):
        """Check if messages need to be assembled and sent; return the
        number of messages queued or None.
        
        This method is guaranteed to be called periodically.
        """

    def trigger(channel):
        """Assemble and queue messages; return the number of messages
        queued.

        A manual override.
        """

class ISubscriptions(interface.Interface):
    """The `subscriptions` attribute of IChannel implements this.

    Allows for adding, removing, and querying subscriptions.
    """
    def add_subscription(
        channel, secret, composer_data, collector_data, metadata):
        """Add a subscription and return it.

        Raises ValueError if subscription already exists.
        """

    def remove_subscription(subscription):
        """Remove subscription.
        """

    def query(**kwargs):
        """Search subscriptions.

        Available fields are: 'fulltext', 'secret', 'format', 'key', 'label'.
        """

class IMessageQueues(IMapping):
    """A dict that contains one ``zc.queue.interfaces.IQueue`` per
    message status.
    """
    messages_sent = schema.Int(
        title=u"Total number of messages sent through this queue",
        )


class IChannel(interface.Interface):
    """A Channel is what we can subscribe to.

    A Channel is a hub of configuration.  It doesn't do anything by
    itself.  Rather, it provides a number of components to configure
    and work with.  It is also the container of subscriptions to it.
    """

    name = schema.ASCIILine(
        title=u"Unique identifier for this channel across the site.",
        )
    
    title = schema.TextLine(
        title=u"Title",
        )

    description = schema.Text(
        title=u"Description"
        )

    scheduler = schema.Object(
        title=u"Scheduler (when)",
        required=False,
        schema=IScheduler,
        )

    collector = schema.Object(
        title=u"Collector (what)",
        required=False,
        schema=ICollector,
        )

    composers = schema.Dict(
        title=u"The channel's composers, keyed by format.",
        key_type=schema.TextLine(title=u"Format"),
        value_type=schema.Object(title=u"Composer", schema=IComposer),
        )

    subscriptions = schema.Object(
        title=u"The channel's subscriptions",
        schema=ISubscriptions,
        )

    queue = schema.Object(
        title=u"This channel's message queues, keyed by message status",
        schema=IMessageQueues,
        )


class IFormatItem(interface.Interface):
    """A view that formats an item for use in a newsletter.

    Given an item as retrieved from a collector, this view returns a
    representation of the given item ready for inclusion in the
    message via the ``IComposer.render`` method.
    """

    def __call__():
        """Returns a unicode-string."""

class ITransform(interface.Interface):
    """Allows to rewrite links and the like.
    """
    def __call__(text, subscription):
        """Return transformed text
        """

class IDispatch(interface.Interface):
    """Dispatchers adapt message *payloads* and send them."""

    def __call__():
        """Attempt to send message.

        Must return a tuple ``(status, status_message)``.  See
        ``MESSAGE_STATES`` for possible choices for the status.  The
        status message may be None or a text containing details about
        the status, e.g. why it failed.

        If this method raises an exception, an 'error' is assumed.
        """

class IChannelLookup(interface.Interface):
    """A utility that looks up all channels in a site.
    """

    def __call__():
        """Return a list of ``IChannel`` objects.
        """

class IFormLayer(z3c.form.interfaces.IFormLayer):
    pass

class IDynamicVocabularyCollection(zope.schema.interfaces.ICollection):
    """ Used to mark ICollection Fields in our dynamic schemas.
        To indicate that thay have dynamic vocabularies.
        We need a more tolerant z3c.form.interfaces.IDataConverter
        in this case - one that drops saved values that are no longer
        in the vocabulary when updating widgets.
        """
