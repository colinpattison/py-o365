from O365.connection import Connection, Protocol, MSGraphProtocol, BasicAuthProtocol, AUTH_METHOD
from O365.utils import ME_RESOURCE
from O365.message import Message
from O365.mailbox import MailBox
from O365.address_book import AddressBook, GlobalAddressList
from O365.calendar import Schedule


class Account(object):
    """ Class helper to integrate all components into a single object """

    def __init__(self, credentials, *, auth_method=AUTH_METHOD.OAUTH, scopes=None,
                 protocol=None, main_resource=ME_RESOURCE, **kwargs):

        if isinstance(auth_method, str):
            try:
                auth_method = AUTH_METHOD(auth_method)
            except ValueError as e:
                raise e

        if auth_method is AUTH_METHOD.BASIC:
            protocol = protocol or BasicAuthProtocol  # using basic auth defaults to Office 365 protocol
            self.protocol = protocol(default_resource=main_resource, **kwargs) if isinstance(protocol, type) else protocol
            if self.protocol.api_version != 'v1.0' or not isinstance(self.protocol, BasicAuthProtocol):
                raise RuntimeError(
                    'Basic Authentication only works with Office 365 Api version v1.0 and until November 1 2018.')
        elif auth_method is AUTH_METHOD.OAUTH:
            protocol = protocol or MSGraphProtocol  # using oauth auth defaults to Graph protocol
            self.protocol = protocol(default_resource=main_resource, **kwargs) if isinstance(protocol, type) else protocol

        if not isinstance(self.protocol, Protocol):
            raise ValueError("'protocol' must be a subclass of Protocol")

        self.con = kwargs.get('connection') or Connection(credentials,
                                                          auth_method=auth_method,
                                                          scopes=self.protocol.get_scopes_for(scopes))

        self.main_resource = main_resource

    @property
    def connection(self):
        """ Alias for self.con """
        return self.con

    def new_message(self, resource=None):
        """
        Creates a new message to be send or stored
        :param resource: Custom resource to be used in this message. defaults to parent main_resource.
        """
        return Message(parent=self, main_resource=resource, is_draft=True)

    def mailbox(self, resource=None):
        """
        Creates MailBox Folder instance
        :param resource: Custom resource to be used in this mailbox. defaults to parent main_resource.
        """
        return MailBox(parent=self, main_resource=resource, name='MailBox')

    def address_book(self, *, resource=None, address_book='personal'):
        """
        Creates Address Book instance
        :param resource: Custom resource to be used in this address book. defaults to parent main_resource.
        :param address_book: Choose from Personal or Gal (Global Address List)
        """
        if address_book == 'personal':
            return AddressBook(parent=self, main_resource=resource, name='Personal Address Book')
        elif address_book == 'gal':
            if self.con.auth_method == AUTH_METHOD.BASIC and self.protocol.api_version == 'v1.0':
                raise RuntimeError('v1.0 with basic Authentication does not have access to the Global Addres List (Users API)')
            return GlobalAddressList(parent=self)
        else:
            raise RuntimeError('Addres_book must be either "personal" (resource address book) or "gal" (Global Address List)')

    def schedule(self, *, resource=None):
        """
        Creates Schedule instance to handle calendars
        :param resource: Custom resource to be used in this schedule object. defaults to parent main_resource.
        """
        return Schedule(parent=self, main_resource=resource)