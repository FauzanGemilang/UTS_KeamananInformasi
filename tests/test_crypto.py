from crypto.encryption import encrypt_message, decrypt_message

def test_encrypt_decrypt():
    msg = "Pesan rahasia SecretPic"
    key = "kunci-demo"
    payload = encrypt_message(msg, key)
    assert decrypt_message(payload, key) == msg

def test_wrong_key():
    payload = encrypt_message("hello", "correct")
    try:
        decrypt_message(payload, "wrong")
        assert False
    except ValueError:
        assert True
