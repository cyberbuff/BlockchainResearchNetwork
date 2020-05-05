from iroha import Iroha, IrohaGrpc
from iroha import IrohaCrypto
import os
import sys
import time
import uuid
import binascii

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')

IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')
ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
ADMIN_PRIVATE_KEY = os.getenv(
    'ADMIN_PRIVATE_KEY', 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70')

iroha = Iroha(ADMIN_ACCOUNT_ID)
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))


def user_pub_priv_key():
    user_private_key = IrohaCrypto.private_key()
    user_public_key = IrohaCrypto.derive_public_key(user_private_key)
    print(user_pub_priv_key)
    return user_private_key, user_public_key


def create_account(name):
    priv,pub = user_pub_priv_key()
    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name=name, domain_id=ADMIN_ACCOUNT_ID.split('@')[1],
                      public_key=pub)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    res = send_transaction_and_print_status(tx)
    return res


def create_asset(journal_id):
    commands = [
        iroha.command('CreateAsset', asset_name=journal_id,
                      domain_id='journal', precision=1)
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    print(send_transaction_and_print_status(tx))


def assign_asset(journal_id):
    create_asset(journal_id)
    assetid = journal_id+'#'+'journal'
    commands = [
        iroha.command('AddAssetQuantity',
                      asset_id=assetid, amount='1'),
        iroha.command('TransferAsset', src_account_id=ADMIN_ACCOUNT_ID, dest_account_id='author@test',
                      asset_id=assetid, description='init top up', amount='1')
    ]
    tx = IrohaCrypto.sign_transaction(iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    return send_transaction_and_print_status(tx)

def get_account_assets(name):
    """
    List all the assets of an account
    """
    accid = name+'@'+ ADMIN_ACCOUNT_ID.split('@')[1]
    query = iroha.query('GetAccountAssets', account_id=accid)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    res = []
    for asset in data:
        res.append(asset)
    return res


def get_account_details(name):
    """
    List all the assets of an account
    """
    accid = name+'@'+ ADMIN_ACCOUNT_ID.split('@')[1]
    print(accid)
    query = iroha.query('GetAccountDetail', account_id=accid)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    res = []
    for asset in data:
        res.append(asset)
    return res


def transfer_from_src_to_dest(src,dest,ass):
    srcaccid = src+'@'+ADMIN_ACCOUNT_ID.split('@')[1]
    destaccid = dest+'@'+ADMIN_ACCOUNT_ID.split('@')[1]
    assetid = ass+'#'+'journal'
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id=srcaccid, dest_account_id=destaccid,
                      asset_id=assetid, description='Transferred', amount='1')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    result = send_transaction_and_print_status(tx)
    return result


def approve_journal(journal_id):
    return transfer_from_src_to_dest('reviewer','public',journal_id)


def reject_journal(journal_id):
    return transfer_from_src_to_dest('reviewer','private',journal_id)


def send_for_approval(journal_id):
    return transfer_from_src_to_dest('author','reviewer',journal_id)


def send_transaction_and_print_status(transaction):
    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    to_send_back = []
    to_send_back.append(hex_hash)
    for status in net.tx_status_stream(transaction):
        to_send_back.append(status)
    return to_send_back

if __name__ == "__main__":
    # create_account("author")
    print(assign_asset('journal2'))
    print(get_account_details("author"))
    print(get_account_assets("author"))
