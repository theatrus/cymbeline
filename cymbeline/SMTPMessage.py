


class SMTPMessage(object):
    def __init__(self, mailfrom = None,
                 rcptto = None, message = []):
        self.mailfrom = mailfrom
        self.rcptto = rcptto
        self.message = message


    def set_client_address(self, client):
        self.client_address = client
        return client

    def set_mailfrom(self, f):
        self.mailfrom = f

    def set_rcptto(self, g):
        self.rcptto = g

    def add_message_line(self, line):
        self.message.append(line)


    def set_id(self, id):
        self.id = id
    
