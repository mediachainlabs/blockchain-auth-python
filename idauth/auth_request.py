import json
import uuid
import time
import traceback
from pybitcoin import BitcoinPublicKey

from .tokenizer import Tokenizer, load_signing_key
from .exceptions import DecodeError
from .permissions import PERMISSION_TYPES


def validate_permissions(permissions):
    # validate permissions
    if not isinstance(permissions, list):
        raise ValueError('"permissions" must be a list')
    invalid_permissions = [
        permission not in PERMISSION_TYPES
        for permission in permissions
    ]
    if any(invalid_permissions):
        raise ValueError('Invalid permission provided')


class AuthRequest():
    """ Interface for creating signed auth request tokens, as well as decoding
        and verifying them.
    """
    tokenizer = Tokenizer()

    def __init__(self, signing_key, verifying_key, issuing_domain,
                 permissions=[]):
        """ signing_key should be provided in PEM format.
            verifying_ey should be provided in compressed hex format.
            issuing_domain should be a valid domain.
            permissions should be a list.
        """
        validate_permissions(permissions)
        self.issuing_domain = issuing_domain
        self.permissions = permissions
        self.signing_key = signing_key
        self.verifying_key = verifying_key

    def _payload(self):
        return {
            'issuer': {
                'domain': self.issuing_domain,
                'publicKey': self.verifying_key
            },
            'issuedAt': str(time.time()),
            'challenge': str(uuid.uuid4()),
            'permissions': self.permissions
        }

    def token(self):
        return self.tokenizer.encode(self._payload(), self.signing_key)

    def json(self):
        return json.loads(self.decode(self.token()))

    @classmethod
    def decode(cls, token, verify=False):
        if not isinstance(token, (str, unicode)):
            raise ValueError('Token must be a string')
        # decode the token without any verification
        decoded_token = cls.tokenizer.decode(token)

        if verify:
            public_key_str = json.loads(decoded_token)['issuer']['publicKey']
            public_key = BitcoinPublicKey(str(public_key_str))
            # decode the token again, this time by performing a verification
            # with the public key we extracted
            decoded_token = cls.tokenizer.decode(token, public_key.to_pem())

        return json.loads(decoded_token)

    @classmethod
    def verify(cls, token):
        if not isinstance(token, (str, unicode)):
            raise ValueError('Token must be a string')
        decoded_token = cls.decode(token, verify=True)
        return True
