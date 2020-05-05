from iroha import Iroha, IrohaGrpc
from iroha import IrohaCrypto
from iroha import primitive_pb2
import os
from functools import wraps
import sys
import time
import uuid
import binascii

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')

IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))

class User:
    def __init__(self,account_id,private_key):
        self.account_id = account_id
        self.private_key = private_key


class IrohaSDK:
    def __init__(self,user):
        if user:
            self.user = user
            self.iroha = Iroha(user.account_id)

    def get_my_roles(self):
        accid = self.user.account_id
        print(accid)
        query = self.iroha.query('GetAccount', account_id=accid)
        IrohaCrypto.sign_query(query, self.user.private_key)
        response = net.send_query(query)
        print(response)
        data = response.account_response.account_roles
        return list(data)

    def is_user(self):
        return 'user' in self.get_my_roles()

    def is_author(self):
        return 'author' in self.get_my_roles()

    def is_admin(self):
        return 'admin' in self.get_my_roles()

    def is_reviewer(self):
        return 'reviewer' in self.get_my_roles()

    def get_account_id(self,name):
        return f'{name}@{self.user.domain}'


    def user_pub_priv_key(self):
        user_private_key = IrohaCrypto.private_key()
        user_public_key = IrohaCrypto.derive_public_key(user_private_key)
        return user_private_key, user_public_key


    def create_account(self,name):
        priv,pub = self.user_pub_priv_key()
        print(name)
        print(priv)
        print(pub)
        tx = self.iroha.transaction([
            self.iroha.command('CreateAccount', account_name=name, domain_id=self.user.domain,
                        public_key=pub)
        ])
        IrohaCrypto.sign_transaction(tx, self.user.private_key)
        res = self.send_transaction_and_print_status(tx)
        return res

    def invalid_permissions(self):
        print('Invalid Permissions')

    
    def create_asset(self,journal_id):
        if self.is_author:
            assetid = f'{journal_id}#journal'
            commands = [
                self.iroha.command('CreateAsset', asset_name=journal_id,
                            domain_id='journal', precision=1),
                self.iroha.command('AddAssetQuantity',
                            asset_id=assetid, amount='1')
            ]
            return self.perform_commands(commands)
        else:
            self.invalid_permissions()

    def get_account_assets(self,name):
        """
        List all the assets of an account
        """
        print(name)
        accid = self.get_account_id(name)
        query = self.iroha.query('GetAccountAssets', account_id=accid)
        IrohaCrypto.sign_query(query, self.user.private_key)

        response = net.send_query(query)
        data = response.account_assets_response.account_assets
        res = []
        for asset in data:
            res.append(asset)
        return res


    def get_account_details(self,name):
        """
        List all the assets of an account
        """
        accid = self.get_account_id(name)
        print(accid)
        query = self.iroha.query('GetAccount', account_id=accid)
        IrohaCrypto.sign_query(query, self.user.private_key)
        response = net.send_query(query)
        print(response)
        data = response.account_response.account
        return data


    def transfer_from_src_to_dest(self,dest,journal_id):
        destaccid = self.get_account_id(dest)
        assetid = f'{journal_id}#journal'
        tx = self.iroha.transaction([
            self.iroha.command('TransferAsset', src_account_id=self.user.account_id, dest_account_id=destaccid,
                        asset_id=assetid, description='Transferred', amount='1')
        ])
        IrohaCrypto.sign_transaction(tx, self.user.private_key)
        result = self.send_transaction_and_print_status(tx)
        return result

    def approve_journal(self,journal_id):
        if self.is_reviewer:
            return self.transfer_from_src_to_dest('public',journal_id)
        else:
            return self.invalid_permissions()


    def reject_journal(self,journal_id):
        if self.is_reviewer:
            return self.transfer_from_src_to_dest('private',journal_id)
        else:
            return self.invalid_permissions()

        

    def send_for_approval(self,journal_id):
        if self.is_author:
            return self.transfer_from_src_to_dest('reviewer',journal_id)
        else:
            return self.invalid_permissions()


    def send_transaction_and_print_status(self,transaction):
        hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
        net.send_tx(transaction)
        to_send_back = []
        to_send_back.append(hex_hash)
        print(transaction)
        for status in net.tx_status_stream(transaction):
            to_send_back.append(status)
        return to_send_back


    def perform_commands(self,commands):
        tx = self.iroha.transaction(commands)
        IrohaCrypto.sign_transaction(tx, self.user.private_key)
        result = self.send_transaction_and_print_status(tx)
        return result


    def perform_query(self,query):
        return None


    def set_account_details(self,name,data):
        acc_id = self.get_account_id(name)
        print(acc_id)
        commands = [self.iroha.command('SetAccountDetail',account_id=acc_id,key=k,value=v) for k,v in data.items()]
        return self.perform_commands(commands)


    def test_case(self,journal_id,approve=True):
        print(self.create_asset(journal_id))
        print("Send for Approval")
        print(self.send_for_approval(journal_id))
        print("Approval")
        if approve:
            return self.approve_journal(journal_id)
        else:
            return self.reject_journal(journal_id)


    def is_logged_in(self):
        return self.is_user()
