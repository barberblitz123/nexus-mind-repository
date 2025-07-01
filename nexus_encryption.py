"""
NEXUS Encryption Services
Comprehensive encryption module with AES-256, RSA, TLS management, and E2E encryption
"""

import os
import base64
import secrets
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import (
    CertificateBuilder, NameOID, Name, Certificate,
    CertificateSigningRequest, CertificateSigningRequestBuilder,
    BasicConstraints, KeyUsage, ExtendedKeyUsage,
    SubjectAlternativeName, DNSName, IPAddress
)
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.fernet import Fernet
import sqlalchemy
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as DBSession
import logging
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()


class EncryptionMethod(Enum):
    """Supported encryption methods"""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    RSA_OAEP = "rsa-oaep"
    RSA_PSS = "rsa-pss"
    FERNET = "fernet"
    CHACHA20_POLY1305 = "chacha20-poly1305"


@dataclass
class EncryptionConfig:
    """Encryption configuration"""
    # Key derivation
    kdf_iterations: int = 100000
    kdf_algorithm: str = "pbkdf2-sha256"
    
    # AES settings
    aes_key_size: int = 256  # bits
    aes_mode: str = "gcm"
    aes_tag_length: int = 16  # bytes
    
    # RSA settings
    rsa_key_size: int = 4096  # bits
    rsa_public_exponent: int = 65537
    
    # Key rotation
    key_rotation_days: int = 90
    key_version_limit: int = 5
    
    # Storage paths
    key_storage_path: Path = Path("./keys")
    cert_storage_path: Path = Path("./certs")
    
    # TLS settings
    tls_min_version: str = "TLSv1.2"
    tls_ciphers: List[str] = field(default_factory=lambda: [
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "ECDHE-ECDSA-AES256-GCM-SHA384",
        "ECDHE-ECDSA-AES128-GCM-SHA256"
    ])
    
    # E2E encryption
    e2e_key_exchange_algorithm: str = "ecdh"
    e2e_session_timeout: int = 3600  # seconds


@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    id: str
    version: int
    algorithm: EncryptionMethod
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    purpose: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EncryptedData:
    """Encrypted data container"""
    ciphertext: bytes
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    key_id: Optional[str] = None
    algorithm: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecretStore(Base):
    """Database model for secret storage"""
    __tablename__ = 'secrets'
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    encrypted_value = Column(Text, nullable=False)
    key_id = Column(String(64), nullable=False)
    algorithm = Column(String(32), nullable=False)
    nonce = Column(String(64))
    tag = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata = Column(Text)  # JSON


class EncryptedField(Base):
    """Database model for encrypted field tracking"""
    __tablename__ = 'encrypted_fields'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(128), nullable=False)
    column_name = Column(String(128), nullable=False)
    record_id = Column(String(128), nullable=False)
    key_id = Column(String(64), nullable=False)
    algorithm = Column(String(32), nullable=False)
    encrypted_at = Column(DateTime, default=datetime.utcnow)


class EncryptionManager:
    """Core encryption manager for NEXUS"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self.keys: Dict[str, EncryptionKey] = {}
        self.rsa_keys: Dict[str, Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]] = {}
        self.active_keys: Dict[str, str] = {}  # purpose -> key_id mapping
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize storage directories
        self.config.key_storage_path.mkdir(parents=True, exist_ok=True)
        self.config.cert_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load or generate master key
        self.master_key = self._load_or_generate_master_key()
        
    def _load_or_generate_master_key(self) -> bytes:
        """Load or generate master encryption key"""
        master_key_path = self.config.key_storage_path / "master.key"
        
        if master_key_path.exists():
            with open(master_key_path, "rb") as f:
                return f.read()
        else:
            # Generate new master key
            master_key = secrets.token_bytes(32)
            
            # Save securely (in production, use hardware security module)
            with open(master_key_path, "wb") as f:
                f.write(master_key)
            
            # Set proper permissions (Unix-like systems)
            os.chmod(master_key_path, 0o600)
            
            logger.info("Generated new master encryption key")
            return master_key
    
    # AES-256 Encryption
    def generate_aes_key(self, purpose: str = "general") -> EncryptionKey:
        """Generate new AES-256 key"""
        key_data = secrets.token_bytes(32)  # 256 bits
        key_id = secrets.token_urlsafe(16)
        
        # Determine version
        existing_keys = [k for k in self.keys.values() if k.purpose == purpose]
        version = max([k.version for k in existing_keys], default=0) + 1
        
        key = EncryptionKey(
            id=key_id,
            version=version,
            algorithm=EncryptionMethod.AES_256_GCM,
            key_data=key_data,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self.config.key_rotation_days),
            purpose=purpose
        )
        
        self.keys[key_id] = key
        self.active_keys[purpose] = key_id
        
        # Save encrypted key
        self._save_key(key)
        
        return key
    
    def encrypt_aes(self, data: Union[str, bytes], key_id: Optional[str] = None) -> EncryptedData:
        """Encrypt data using AES-256-GCM"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Get key
        if not key_id:
            key_id = self.active_keys.get("general")
        key = self.keys.get(key_id)
        
        if not key:
            raise ValueError(f"Key not found: {key_id}")
            
        # Generate nonce
        nonce = secrets.token_bytes(12)  # 96 bits for GCM
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key.key_data),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=encryptor.tag,
            key_id=key_id,
            algorithm=EncryptionMethod.AES_256_GCM.value
        )
    
    def decrypt_aes(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt AES-256-GCM encrypted data"""
        key = self.keys.get(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Key not found: {encrypted_data.key_id}")
            
        cipher = Cipher(
            algorithms.AES(key.key_data),
            modes.GCM(encrypted_data.nonce, encrypted_data.tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
        
        return plaintext
    
    # RSA Key Management
    def generate_rsa_keypair(self, purpose: str = "general") -> Tuple[str, rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generate RSA key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=self.config.rsa_public_exponent,
            key_size=self.config.rsa_key_size,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        key_id = secrets.token_urlsafe(16)
        
        self.rsa_keys[key_id] = (private_key, public_key)
        
        # Save keys
        self._save_rsa_keys(key_id, private_key, public_key, purpose)
        
        return key_id, private_key, public_key
    
    def encrypt_rsa(self, data: Union[str, bytes], public_key: rsa.RSAPublicKey) -> bytes:
        """Encrypt data using RSA-OAEP"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return ciphertext
    
    def decrypt_rsa(self, ciphertext: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        """Decrypt RSA-OAEP encrypted data"""
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return plaintext
    
    # Secure Secret Storage
    def store_secret(self, name: str, value: str, expires_in_days: Optional[int] = None) -> str:
        """Store secret securely"""
        # Encrypt secret
        encrypted = self.encrypt_aes(value)
        
        secret_id = secrets.token_urlsafe(16)
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            
        # Store in database (would need DB session in real implementation)
        secret = {
            'id': secret_id,
            'name': name,
            'encrypted_value': base64.b64encode(encrypted.ciphertext).decode(),
            'key_id': encrypted.key_id,
            'algorithm': encrypted.algorithm,
            'nonce': base64.b64encode(encrypted.nonce).decode() if encrypted.nonce else None,
            'tag': base64.b64encode(encrypted.tag).decode() if encrypted.tag else None,
            'expires_at': expires_at
        }
        
        logger.info(f"Stored secret: {name}")
        return secret_id
    
    def retrieve_secret(self, name: str) -> Optional[str]:
        """Retrieve and decrypt secret"""
        # In real implementation, query from database
        # For now, return placeholder
        return None
    
    # Database Field Encryption
    def encrypt_field(self, value: Any, field_type: type = str) -> str:
        """Encrypt database field value"""
        # Serialize non-string values
        if not isinstance(value, str):
            value = json.dumps(value)
            
        encrypted = self.encrypt_aes(value)
        
        # Combine encrypted data into storable format
        encrypted_value = {
            'ct': base64.b64encode(encrypted.ciphertext).decode(),
            'n': base64.b64encode(encrypted.nonce).decode() if encrypted.nonce else None,
            't': base64.b64encode(encrypted.tag).decode() if encrypted.tag else None,
            'k': encrypted.key_id,
            'a': encrypted.algorithm
        }
        
        return base64.b64encode(json.dumps(encrypted_value).encode()).decode()
    
    def decrypt_field(self, encrypted_value: str, field_type: type = str) -> Any:
        """Decrypt database field value"""
        try:
            # Decode encrypted value
            encrypted_data = json.loads(base64.b64decode(encrypted_value))
            
            # Reconstruct EncryptedData
            encrypted = EncryptedData(
                ciphertext=base64.b64decode(encrypted_data['ct']),
                nonce=base64.b64decode(encrypted_data['n']) if encrypted_data.get('n') else None,
                tag=base64.b64decode(encrypted_data['t']) if encrypted_data.get('t') else None,
                key_id=encrypted_data['k'],
                algorithm=encrypted_data['a']
            )
            
            # Decrypt
            plaintext = self.decrypt_aes(encrypted).decode('utf-8')
            
            # Deserialize if needed
            if field_type != str:
                return json.loads(plaintext)
                
            return plaintext
            
        except Exception as e:
            logger.error(f"Failed to decrypt field: {e}")
            raise
    
    # TLS Certificate Management
    def generate_self_signed_certificate(self, common_name: str, 
                                       san_names: Optional[List[str]] = None,
                                       validity_days: int = 365) -> Tuple[Certificate, rsa.RSAPrivateKey]:
        """Generate self-signed TLS certificate"""
        # Generate key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Certificate details
        subject = issuer = Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NEXUS"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        # Build certificate
        builder = CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(private_key.public_key())
        builder = builder.serial_number(int.from_bytes(secrets.token_bytes(16), 'big'))
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
        
        # Add extensions
        builder = builder.add_extension(
            BasicConstraints(ca=True, path_length=0),
            critical=True
        )
        
        builder = builder.add_extension(
            KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=True,
                key_agreement=False,
                content_commitment=False,
                data_encipherment=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        
        # Add SAN if provided
        if san_names:
            san_list = [DNSName(name) for name in san_names]
            builder = builder.add_extension(
                SubjectAlternativeName(san_list),
                critical=False
            )
        
        # Sign certificate
        certificate = builder.sign(private_key, hashes.SHA256(), default_backend())
        
        # Save certificate and key
        cert_path = self.config.cert_storage_path / f"{common_name}.crt"
        key_path = self.config.cert_storage_path / f"{common_name}.key"
        
        with open(cert_path, "wb") as f:
            f.write(certificate.public_bytes(serialization.Encoding.PEM))
            
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"Generated self-signed certificate for {common_name}")
        return certificate, private_key
    
    def generate_csr(self, common_name: str, organization: str, 
                    country: str = "US") -> Tuple[CertificateSigningRequest, rsa.RSAPrivateKey]:
        """Generate certificate signing request"""
        # Generate key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Build CSR
        subject = Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        builder = CertificateSigningRequestBuilder()
        builder = builder.subject_name(subject)
        
        # Sign CSR
        csr = builder.sign(private_key, hashes.SHA256(), default_backend())
        
        return csr, private_key
    
    # End-to-End Encryption
    def generate_e2e_keypair(self, user_id: str) -> Dict[str, str]:
        """Generate E2E encryption keypair for user"""
        # Generate RSA keypair for E2E
        key_id, private_key, public_key = self.generate_rsa_keypair(f"e2e_{user_id}")
        
        # Export public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return {
            'key_id': key_id,
            'public_key': public_pem,
            'algorithm': 'rsa-oaep'
        }
    
    def encrypt_e2e_message(self, message: str, recipient_public_key: str) -> Dict[str, Any]:
        """Encrypt message for E2E communication"""
        # Generate ephemeral AES key
        aes_key = secrets.token_bytes(32)
        
        # Encrypt message with AES
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(secrets.token_bytes(12)),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
        
        # Load recipient's public key
        public_key = serialization.load_pem_public_key(
            recipient_public_key.encode(),
            backend=default_backend()
        )
        
        # Encrypt AES key with recipient's public key
        encrypted_key = self.encrypt_rsa(aes_key, public_key)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'encrypted_key': base64.b64encode(encrypted_key).decode(),
            'nonce': base64.b64encode(cipher.algorithm.nonce).decode(),
            'tag': base64.b64encode(encryptor.tag).decode(),
            'algorithm': 'aes-256-gcm'
        }
    
    def decrypt_e2e_message(self, encrypted_message: Dict[str, Any], private_key_id: str) -> str:
        """Decrypt E2E encrypted message"""
        # Get private key
        private_key, _ = self.rsa_keys.get(private_key_id)
        if not private_key:
            raise ValueError("Private key not found")
            
        # Decrypt AES key
        encrypted_key = base64.b64decode(encrypted_message['encrypted_key'])
        aes_key = self.decrypt_rsa(encrypted_key, private_key)
        
        # Decrypt message
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(
                base64.b64decode(encrypted_message['nonce']),
                base64.b64decode(encrypted_message['tag'])
            ),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(base64.b64decode(encrypted_message['ciphertext']))
        plaintext += decryptor.finalize()
        
        return plaintext.decode('utf-8')
    
    # Key Rotation
    async def rotate_keys(self):
        """Rotate encryption keys"""
        logger.info("Starting key rotation")
        
        for purpose, key_id in self.active_keys.items():
            key = self.keys.get(key_id)
            if not key:
                continue
                
            # Check if key needs rotation
            if key.expires_at and key.expires_at < datetime.now(timezone.utc):
                # Generate new key
                new_key = self.generate_aes_key(purpose)
                logger.info(f"Rotated key for purpose: {purpose}")
                
                # Re-encrypt data with new key (in production)
                # This would involve scanning database for encrypted data
                # and re-encrypting with new key
                
        logger.info("Key rotation completed")
    
    # Helper methods
    def _save_key(self, key: EncryptionKey):
        """Save encryption key securely"""
        # Encrypt key with master key before storage
        encrypted_key = self.encrypt_aes(key.key_data, self.active_keys.get("master"))
        
        key_data = {
            'id': key.id,
            'version': key.version,
            'algorithm': key.algorithm.value,
            'encrypted_key': base64.b64encode(encrypted_key.ciphertext).decode(),
            'nonce': base64.b64encode(encrypted_key.nonce).decode() if encrypted_key.nonce else None,
            'tag': base64.b64encode(encrypted_key.tag).decode() if encrypted_key.tag else None,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat() if key.expires_at else None,
            'purpose': key.purpose,
            'metadata': key.metadata
        }
        
        key_path = self.config.key_storage_path / f"{key.id}.json"
        with open(key_path, "w") as f:
            json.dump(key_data, f)
            
        os.chmod(key_path, 0o600)
    
    def _save_rsa_keys(self, key_id: str, private_key: rsa.RSAPrivateKey, 
                      public_key: rsa.RSAPublicKey, purpose: str):
        """Save RSA keypair"""
        # Encrypt private key with master key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(self.master_key)
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Save keys
        private_path = self.config.key_storage_path / f"{key_id}_private.pem"
        public_path = self.config.key_storage_path / f"{key_id}_public.pem"
        
        with open(private_path, "wb") as f:
            f.write(private_pem)
        os.chmod(private_path, 0o600)
        
        with open(public_path, "wb") as f:
            f.write(public_pem)
        os.chmod(public_path, 0o644)
    
    # Utility functions
    def generate_random_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: Union[str, bytes], algorithm: str = "sha256") -> str:
        """Hash data using specified algorithm"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        if algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data).hexdigest()
        elif algorithm == "blake2b":
            return hashlib.blake2b(data).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks"""
        return secrets.compare_digest(a, b)


# Example usage
if __name__ == "__main__":
    # Initialize encryption manager
    config = EncryptionConfig()
    encryption = EncryptionManager(config)
    
    # Example: Generate AES key
    aes_key = encryption.generate_aes_key("data_encryption")
    print(f"Generated AES key: {aes_key.id}")
    
    # Example: Encrypt/decrypt data
    plaintext = "Sensitive data that needs encryption"
    encrypted = encryption.encrypt_aes(plaintext)
    print(f"Encrypted data: {base64.b64encode(encrypted.ciphertext).decode()[:32]}...")
    
    decrypted = encryption.decrypt_aes(encrypted)
    print(f"Decrypted data: {decrypted.decode()}")
    
    # Example: Generate RSA keypair
    rsa_key_id, private_key, public_key = encryption.generate_rsa_keypair("api_signing")
    print(f"Generated RSA keypair: {rsa_key_id}")
    
    # Example: RSA encryption
    rsa_plaintext = "Secret message"
    rsa_encrypted = encryption.encrypt_rsa(rsa_plaintext, public_key)
    rsa_decrypted = encryption.decrypt_rsa(rsa_encrypted, private_key)
    print(f"RSA decrypted: {rsa_decrypted.decode()}")
    
    # Example: Store secret
    secret_id = encryption.store_secret("api_key", "sk_live_abcdef123456")
    print(f"Stored secret with ID: {secret_id}")
    
    # Example: Database field encryption
    encrypted_field = encryption.encrypt_field({"user_id": 123, "balance": 1000.50}, dict)
    print(f"Encrypted field: {encrypted_field[:32]}...")
    
    # Example: Generate self-signed certificate
    cert, cert_key = encryption.generate_self_signed_certificate(
        "nexus.local",
        san_names=["www.nexus.local", "api.nexus.local"]
    )
    print("Generated self-signed certificate for nexus.local")
    
    # Example: E2E encryption
    e2e_keys = encryption.generate_e2e_keypair("user123")
    print(f"Generated E2E keypair: {e2e_keys['key_id']}")
    
    # Encrypt E2E message
    e2e_encrypted = encryption.encrypt_e2e_message(
        "Hello, this is an end-to-end encrypted message!",
        e2e_keys['public_key']
    )
    print(f"E2E encrypted message: {e2e_encrypted['ciphertext'][:32]}...")
    
    # Example: Generate secure token
    token = encryption.generate_random_token()
    print(f"Generated secure token: {token}")
    
    # Example: Hash data
    hash_value = encryption.hash_data("password123", "sha256")
    print(f"SHA256 hash: {hash_value}")