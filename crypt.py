# python crypt.py
# python -m uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile=key.pem --ssl-certfile=cert.pem                  (запуск )
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import os

KEY_FILE = "key.pem"
CERT_FILE = "cert.pem"

def generate_key_and_cert():
    # Проверка наличия файлов
    if os.path.exists(KEY_FILE) and os.path.exists(CERT_FILE):
        print("🔐 Ключ и сертификат уже существуют.")
        return

    # Генерация приватного ключа
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Сохранение приватного ключа
    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Создание самоподписанного сертификата
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BY"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Minsk"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Minsk"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyApp"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False
    ).sign(key, hashes.SHA256(), default_backend())

    # Сохранение сертификата
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("✅ Ключ и сертификат успешно созданы.")

if __name__ == "__main__":
    generate_key_and_cert()
